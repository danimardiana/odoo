# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from calendar import monthrange
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import fields, models, _


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_invoiced = fields.Boolean(string='invoiced')

    def _prepare_invoice_line(self):
        vals = super(SaleOrderLine, self)._prepare_invoice_line()
        if not vals:
            return vals
        lang = self.order_id.partner_invoice_id.lang
        format_date = self.env['ir.qweb.field.date'].with_context(
            lang=lang).value_to_html
        if self.order_id.clx_invoice_policy_id:
            policy = self.order_id.clx_invoice_policy_id.policy_type
            if policy == 'advance':
                num_of_month = self.order_id.clx_invoice_policy_id.num_of_month + 1
                date_start = self.start_date
                date_end = date_start + relativedelta(
                    months=num_of_month) if not self.end_date else \
                    self.end_date
                date_difference = (date_end - date_start)
                period_msg = _("Invoicing period: %s - %s") % (
                    format_date(fields.Date.to_string(date_start), {}),
                    format_date(
                        fields.Date.to_string(
                            self.end_date if (date_difference.days in (
                                30, 31)) and self.end_date else date_end)
                        , {}
                    )
                )
                vals.update({
                    'name': period_msg,
                    'quantity':
                        self.product_uom_qty if date_difference.days in (
                            30, 31
                        ) else self.product_uom_qty * num_of_month
                })
            elif policy.lower() == 'arrears':
                today = date.today()
                date_start = today.replace(day=1)
                date_end = date_start + relativedelta(months=1, days=-1)
                period_msg = _("Invoicing period: %s - %s") % (format_date(
                    fields.Date.to_string(date_start), {}
                ), format_date(fields.Date.to_string(date_end), {}))
                vals.update({
                    'name': period_msg,
                    'subscription_start_date': date_start,
                    'subscription_end_date': date_end,
                })
        return vals

    def _prepare_subscription_line_data(self):
        """
        inherited method because set interval date on subscription line
        """
        res = super(SaleOrderLine, self)._prepare_subscription_line_data()
        if self.order_id and self.order_id.clx_invoice_policy_id and \
                self.order_id.clx_invoice_policy_id.policy_type == 'advance':
            date_start = self.start_date
            invoice_month = self.order_id.clx_invoice_policy_id and \
                            self.order_id.clx_invoice_policy_id.num_of_month
            if self.line_type == 'base':
                date_start = date_start.replace(day=1)
                date_end = date_start + relativedelta(
                    months=invoice_month + 1, days=-1)
            else:
                date_end = date_start + relativedelta(
                    months=invoice_month)
                date_end = date_end.replace(
                    day=monthrange(date_end.year, date_end.month)[1])
            res[0][-1].update({
                'invoice_start_date': date_start,
                'invoice_end_date': date_end,
            })
        return res
