# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from calendar import monthrange
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import fields, models, _


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
        return (end.year - start.year) * 12 + end.month - start.month

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

    def _prepare_invoice_line(self):
        """
        Prepare the dict of values to create the new invoice line.
        :return: Dictionary of formatted values
        """
        self.ensure_one()
        line = self.so_line_id
        today = date.today()
        date_start = today.replace(day=1)
        date_end = date_start + relativedelta(months=1, days=-1)
        period_msg = self._format_period_msg(date_start, date_end, line)
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
            'quantity': line.qty_to_invoice,
            'discount': self.discount,
            'price_unit': self.price_unit * (
                2 if self.line_type == 'upsell' and
                     not self.last_invoiced and
                     (not self.end_date or
                      self.end_date.month > today.month) else 1
            ),
            'tax_ids': [(6, 0, line.tax_id.ids)],
            'analytic_account_id': line.order_id.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
            'line_type': self.line_type
        }

        if line.display_type:
            res['account_id'] = False
        if self._context.get('advance', False):
            policy_month = self.so_line_id.order_id.clx_invoice_policy_id.num_of_month
            if self.line_type == 'base':
                date_start = today.replace(day=1)
                date_end = date_start + relativedelta(
                    months=policy_month + 1, days=-1)
            else:
                date_start = self.start_date
                date_end = date_start + relativedelta(
                    months=policy_month)
                date_end = date_end.replace(
                    day=monthrange(date_end.year, date_end.month)[1])
            product_qty = self.get_date_month(
                self.invoice_end_date, self.invoice_start_date)
            period_msg = self._format_period_msg(
                date_start, date_end, line,
                date_start, self.invoice_end_date)
            vals = {
                'last_invoiced': today,
                'invoice_start_date': False,
                'invoice_end_date': False,
            }
            expire_date = (date_end + relativedelta(
                months=policy_month + 2)).replace(day=1) + relativedelta(days=-1)
            if self.end_date and self.end_date > date_end:
                vals.update({
                    'invoice_start_date': (
                            date_end + relativedelta(months=1)).replace(day=1),
                    'invoice_end_date': expire_date
                })
            self.write(vals)
            res.update({
                'name': period_msg,
                'subscription_end_date': self.end_date if self.end_date > date_end else expire_date,
                # 'price_unit': self.price_unit * (product_qty + 1)
                'price_unit': self.price_unit * (
                    2 if self.line_type == 'upsell' and
                         not self.last_invoiced and (
                                 not self.end_date or
                                 self.end_date.month > today.month
                         ) else 1
                ) * (product_qty + 1),
            })
        return res
