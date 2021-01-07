# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.


from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta
from collections import OrderedDict
from dateutil import parser


class GenerateInvoiceDateRange(models.TransientModel):
    _name = "generate.invoice.date.range"

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
            lambda sl: (sl.so_line_id.order_id.clx_invoice_policy_id.policy_type == 'advance'))
        end_date_adv_lines = advance_lines.filtered(lambda x: x.end_date and self.end_date <= x.end_date)
        # end_date_not_adv_lines = advance_lines.filtered(lambda x: not x.end_date)
        # print(end_date_not_adv_lines)
        # print(end_date_adv_lines)
        advance_lines = advance_lines.filtered(
            lambda x: x.start_date and x.invoice_start_date and x.invoice_start_date <= self.start_date)
        advance_lines += end_date_adv_lines
        lang = partner_id.lang
        format_date = self.env['ir.qweb.field.date'].with_context(
            lang=lang).value_to_html
        period_msg = ("Invoicing period: %s - %s") % (
            format_date(fields.Date.to_string(self.start_date), {}),
            format_date(fields.Date.to_string(self.end_date), {}))
        account_move_lines = self.env['account.move.line'].search(
            [('partner_id', '=', partner_id.id), ('name', '=', period_msg), ('parent_state', '=', 'draft')])
        if account_move_lines:
            advance_lines = advance_lines.filtered(lambda x: x.id not in account_move_lines.subscription_lines_ids.ids)
        if not advance_lines:
            raise UserError(_("Invoice is created or posted Please check all invoices of this Customer"))
        if advance_lines:
            count = 1
            if partner_id.invoice_creation_type == 'separate':
                count = len(OrderedDict(((self.start_date + timedelta(_)).strftime("%B-%Y"), 0) for _ in
                                        range((self.end_date - self.start_date).days)))
            for i in range(0, count):
                partner_id.with_context(generate_invoice_date_range=True, start_date=self.start_date,
                                        end_date=self.end_date,
                                        ).generate_advance_invoice(
                    advance_lines)
