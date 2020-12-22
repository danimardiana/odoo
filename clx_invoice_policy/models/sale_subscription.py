# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from calendar import monthrange
from datetime import date
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
from datetime import timedelta
from odoo import fields, models, api, _


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    clx_invoice_policy_id = fields.Many2one(
        'clx.invoice.policy', string='Invoice Policy')

    def _compute_invoice_count(self):
        invoice = self.env['account.move']
        can_read = invoice.check_access_rights('read', raise_exception=False)
        for subscription in self:
            subscription.invoice_count = can_read and invoice.search_count([
                '|',
                ('invoice_line_ids.subscription_id', '=', subscription.id),
                ('invoice_line_ids.subscription_ids', 'in', subscription.id)
            ]) or 0

    def action_subscription_invoice(self):
        self.ensure_one()
        invoices = self.env['account.move'].search([
            '|', ('invoice_line_ids.subscription_id', 'in', self.ids),
            ('invoice_line_ids.subscription_ids', 'in', self.id)
        ])
        action = self.env.ref(
            'account.action_move_out_invoice_type').read()[0]
        action["context"] = {"create": False}
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


class SaleSubscriptionLine(models.Model):
    """
    Inherited to setup fields for invoice like.
        Start & End Date : Shows invoice cycle
        Last Invoiced: To store last invoice generated date
    """
    _inherit = "sale.subscription.line"

    last_invoiced = fields.Date(string='Last Invoiced')
    invoice_start_date = fields.Date('Start Date')
    invoice_end_date = fields.Date('End Date')
    cancel_invoice_start_date = fields.Date('Cancel Start Date')
    cancel_invoice_end_date = fields.Date('Cancel End Date')
    account_id = fields.Many2one('account.move', string="Invoice")

    @api.depends('price_unit', 'quantity', 'discount', 'analytic_account_id.pricelist_id')
    def _compute_price_subtotal(self):
        AccountTax = self.env['account.tax']
        for line in self:
            price = AccountTax._fix_tax_included_price(line.price_unit, line.product_id.sudo().taxes_id, AccountTax)
            line.price_subtotal = line.quantity * price * (100.0 - line.discount) / 100.0
            if line.analytic_account_id.partner_id.management_company_type_id.is_flat_discount:
                line.price_subtotal = line.quantity * (
                        price - line.analytic_account_id.partner_id.management_company_type_id.flat_discount)
            if line.analytic_account_id.pricelist_id.sudo().currency_id:
                line.price_subtotal = line.analytic_account_id.pricelist_id.sudo().currency_id.round(
                    line.price_subtotal)

    def start_in_next(self):
        """
        To map with invoice and service start date of to manage Advance + N
        Amount will be calculated bases on Current month and if any service start with advance month it will consider in invoice
        For example:    Advance + 2  Current Month August then invoice will August + September + October\n
                        Start      - End        Amount = Total \n
                        08/01/2020 - 10/31/2020 1000   = 3000 \n
                        09/01/2020 - 12/31/2021 500    = 1000 \n
                        10/01/2020 - 02/28/2021 300    = 0300 \n
                                                         4300 \n
        :return: Total number of months.
        """
        ad_lines = self.env['sale.subscription.line']
        today = date.today().replace(day=1)
        # policy_month = self.so_line_id.order_id.clx_invoice_policy_id.num_of_month
        end_date = today + relativedelta(months=1, days=-1)
        return 0 if self.invoice_start_date > end_date else 1

    def get_date_month(self, end, start):
        """
        To get interval between dates in month to compute invoices
        Formula    : (end.year - start.year) * 12 + end.month - start.month \n
        For example:    Start      - End        = Difference \n
                        08/10/2020 - 10/31/2020 = 2 \n
                        09/15/2020 - 12/31/2021 = 4 \n
                        10/10/2020 - 02/28/2021 = 5 \n
        :param end: Last date of interval
        :param start: Start date of interval
        :return: Total number of months
        """

        return len(OrderedDict(((start + timedelta(_)).strftime("%B-%Y"), 0) for _ in range((end - start).days)))
        # return (end.year - start.year) * 12 + end.month - start.month

    def _format_period_msg(self, date_start, date_end, line, inv_start=False, inv_end=False):
        """
        To calculate invoice period/adjustment date
        :return: Formatted String
        """
        lang = line.order_id.partner_invoice_id.lang
        format_date = self.env['ir.qweb.field.date'].with_context(
            lang=lang).value_to_html
        if line.order_id.clx_invoice_policy_id.policy_type == 'advance' and \
                self.line_type == 'upsell' and not self.last_invoiced:
            return '%s: %s - %s' % (
                _("Invoice Adjustment"),
                format_date(fields.Date.to_string(inv_start), {}),
                format_date(fields.Date.to_string(inv_end), {}))
        elif line.order_id.clx_invoice_policy_id.policy_type == 'arrears':
            return '%s: %s - %s' % (
                _("Invoicing period"),
                format_date(fields.Date.to_string(date_start), {}),
                format_date(fields.Date.to_string(date_end), {}))
        elif inv_start and inv_end:
            return '%s: %s - %s' % (
                _("Invoicing period"),
                format_date(fields.Date.to_string(inv_start), {}),
                format_date(fields.Date.to_string(inv_end), {}))
        else:
            return '%s: %s - %s' % (
                _("Invoicing period"),
                format_date(fields.Date.to_string(date_start), {}),
                format_date(fields.Date.to_string(date_end), {}))

    def _prepare_invoice_line(self):
        """
        Prepare the dict of values to create the new invoice line.
        :return: Dictionary of formatted values
        """
        self.ensure_one()
        line = self.so_line_id
        today = date.today()
        date_start = line.start_date
        date_end = date_start + relativedelta(months=1, days=-1)
        period_msg = self._format_period_msg(date_start, date_end, line, self.invoice_start_date, self.invoice_end_date)
        discount = line.discount
        policy_month = self.so_line_id.order_id.clx_invoice_policy_id.num_of_month + 1
        if line.order_id.partner_id.management_company_type_id.is_flat_discount:
            flat_discount = line.order_id.partner_id.management_company_type_id.flat_discount
            discount = (flat_discount / line.price_unit) * 100
        res = {
            'display_type': line.display_type,
            'sequence': line.sequence,
            'name': period_msg,
            'subscription_id': self.analytic_account_id.id,
            'subscription_ids': [(6, 0, self.analytic_account_id.ids)],
            'subscription_start_date': self.start_date,
            'subscription_end_date': date_end,
            'product_id': self.product_id.id,
            'category_id': self.product_id.categ_id.id,
            'product_uom_id': line.product_uom.id,
            'quantity': 1,
            'discount': discount,
            'price_unit': self.price_unit * (
                2 if self.line_type == 'upsell' and
                     not self.last_invoiced and
                     (not self.end_date or
                      self.end_date.month > today.month) else 1
            ),
            'tax_ids': [(6, 0, line.tax_id.ids)],
            'analytic_account_id': line.order_id.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
            'line_type': self.line_type,
            'sale_line_ids': line.ids,
            'management_fees': line.management_price * (
                2 if self.line_type == 'upsell' and
                     not self.last_invoiced and
                     (not self.end_date or
                      self.end_date.month > today.month) else 1
            ),
            'wholesale': line.wholesale_price * (
                2 if self.line_type == 'upsell' and
                     not self.last_invoiced and
                     (not self.end_date or
                      self.end_date.month > today.month) else 1
            ),
        }
        if line.display_type:
            res['account_id'] = False
        if self._context.get('advance', False):
            product_qty = 1
            end_date = self.invoice_end_date
            if self.so_line_id.order_id.partner_id.invoice_creation_type == 'separate':
                policy_month = 1
            period_msg = self._format_period_msg(
                date_start, date_end, line, self.invoice_start_date, self.invoice_end_date)
            vals = {
                'last_invoiced': today,
                'invoice_start_date': False,
                'invoice_end_date': False,
            }
            expire_date = False
            if self.invoice_end_date:
                expire_date = (self.invoice_end_date + relativedelta(
                    months=policy_month + 1)).replace(day=1) + relativedelta(days=-1)
            if not self.end_date:
                vals.update({
                    'invoice_start_date': (self.invoice_end_date + relativedelta(months=1)).replace(
                        day=1) if self.invoice_end_date else False,
                    'invoice_end_date': expire_date
                })
                if line.product_id.subscription_template_id.recurring_rule_type == 'yearly':
                    yearly_start_date = (self.invoice_end_date + relativedelta(months=1)).replace(
                        day=1) if self.invoice_end_date else False
                    yearly_end_date = (yearly_start_date + relativedelta(
                        months=12)).replace(day=1) + relativedelta(days=-1)
                    vals.update({
                        'invoice_end_date': yearly_end_date
                    })
                    lang = line.order_id.partner_invoice_id.lang
                    format_date = self.env['ir.qweb.field.date'].with_context(
                        lang=lang).value_to_html
                    period_msg = ("Invoicing period: %s - %s") % (
                        format_date(fields.Date.to_string(self.invoice_start_date), {}),
                        format_date(fields.Date.to_string(self.invoice_end_date), {}))
            self.write(vals)
            res.update({
                'name': period_msg,
                'subscription_end_date': self.end_date if self.end_date and self.end_date > date_end else expire_date,
                'price_unit': self.price_unit * (
                    2 if self.line_type == 'upsell' and
                         not self.last_invoiced and (
                                 not self.end_date or
                                 self.end_date.month > today.month
                         ) else 1
                ) * product_qty,
            })

            r = end_date - line.start_date
            if r.days + 1 in (30, 31, 28):
                return res
            if r.days < 30 or r.days < 31:
                per_day_price = line.price_unit / end_date.day
                new_price = per_day_price * r.days
                per_day_management_price = line.management_price / end_date.day
                new_management_price = per_day_management_price * r.days
                res.update({
                    'price_unit': new_price,
                    'management_fees': new_management_price,
                    'wholesale': new_price - new_management_price,
                })

        if line.product_id.subscription_template_id.recurring_rule_type == 'yearly':
            res.update({
                'name': period_msg,
                'price_unit': self.price_unit * 12
            })
        return res
