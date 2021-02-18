# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.


from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta
from collections import OrderedDict
from dateutil.relativedelta import relativedelta
import datetime


class GenerateInvoiceDateRange(models.TransientModel):
    _name = "generate.invoice.date.range"
    _description = "Generate Invoice Date Range"

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')

    @api.onchange('start_date', 'end_date')
    def onchange_date_validation(self):
        if self.start_date and self.end_date and \
                self.start_date >= self.end_date:
            raise UserError(_("Invalid date range."))

    def generate_invoice(self):
        partner_id = self.env['res.partner'].search([('id', '=', self._context.get('active_id'))])
        if partner_id:
            lines = self.env['sale.subscription.line'].search([
                ('so_line_id.order_id.partner_id', 'child_of', partner_id.id),
                ('so_line_id.order_id.state', 'in', ('sale', 'done')),
            ])
            if not lines:
                raise UserError(_("You need to sale order for create a invoice!!"))
        advance_lines = lines.filtered(
            lambda sl: (
                    sl.so_line_id.order_id.clx_invoice_policy_id.policy_type == 'advance' and sl.product_id.subscription_template_id.recurring_rule_type == "monthly"))
        final_adv_line = self.env['sale.subscription.line']
        for adv_line in advance_lines:
            if not adv_line.end_date and self.end_date >= adv_line.start_date:
                final_adv_line += adv_line
            elif adv_line.end_date and self.start_date <= adv_line.end_date:
                final_adv_line += adv_line
        advance_lines = final_adv_line
        lang = partner_id.lang
        format_date = self.env['ir.qweb.field.date'].with_context(
            lang=lang).value_to_html
        period_msg = ("Invoicing period: %s - %s") % (
            format_date(fields.Date.to_string(self.start_date), {}),
            format_date(fields.Date.to_string(self.end_date), {}))
        account_move_lines = self.env['account.move.line'].search(
            [('partner_id', '=', partner_id.id), ('name', '=', period_msg), ('parent_state', 'in', ('draft', 'posted')),
             ('subscription_lines_ids', 'in', advance_lines.ids)])
        yearly_advance_lines = lines.filtered(
            lambda sl: (
                    sl.so_line_id.order_id.clx_invoice_policy_id.policy_type == 'advance' and sl.product_id.subscription_template_id.recurring_rule_type == "yearly"))
        if yearly_advance_lines:
            all_account_move_lines = self.env['account.move.line'].search(
                [('partner_id', '=', partner_id.id),
                 ('parent_state', 'in', ('draft', 'posted')),
                 ])
            for y_line in yearly_advance_lines:
                count = len(OrderedDict(((self.start_date + timedelta(_)).strftime("%B-%Y"), 0) for _ in
                                        range((self.end_date - self.start_date).days)))
                if period_msg not in all_account_move_lines.mapped('name') and (
                        count == 12 or y_line.start_date.month == self.start_date.month):
                    advance_lines += y_line
        if account_move_lines:
            for ad_line in advance_lines:
                if ad_line.id in account_move_lines.mapped('subscription_lines_ids').ids:
                    advance_lines -= ad_line
            # raise UserError(_("Invoice of This period {} is Already created").format(period_msg))
        if advance_lines:
            advance_lines = advance_lines.filtered(lambda x: x.price_unit > 0)
            advance_lines_list = list(set(advance_lines.ids))
            advance_lines = self.env['sale.subscription.line'].browse(advance_lines_list)
            count = 1
            if partner_id.invoice_creation_type == 'separate':
                count = len(OrderedDict(((self.start_date + timedelta(_)).strftime("%B-%Y"), 0) for _ in
                                        range((self.end_date - self.start_date).days)))
            next_month_date = self.start_date
            start_date = self.start_date
            end_date = self.end_date
            for i in range(0, count):
                next_month_date = next_month_date + relativedelta(months=1)
                if partner_id.invoice_selection == 'sol':
                    partner_id.with_context(generate_invoice_date_range=True, start_date=start_date,
                                            end_date=end_date, sol=True,
                                            ).generate_advance_invoice(
                        advance_lines)
                else:
                    partner_id.with_context(generate_invoice_date_range=True, start_date=start_date,
                                            end_date=end_date,
                                            ).generate_advance_invoice(
                        advance_lines)

                all_lines = self.env['sale.subscription.line'].browse(advance_lines_list)
                for adv_line in all_lines:
                    if adv_line.product_id.subscription_template_id.recurring_rule_type == "yearly" and adv_line.invoice_start_date == next_month_date:
                        advance_lines += adv_line
                    elif adv_line.product_id.subscription_template_id.recurring_rule_type == "yearly":
                        advance_lines -= adv_line
                start_date = start_date + relativedelta(months=1)
                end_date = end_date + relativedelta(months=1)
