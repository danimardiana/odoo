# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from calendar import monthrange
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import fields, models, api, _


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_invoiced = fields.Boolean(string='invoiced')

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            if line.order_id.partner_id.management_company_type_id and line.order_id.partner_id.management_company_type_id.is_flat_discount:
                price = line.price_unit - line.order_id.partner_id.management_company_type_id.flat_discount
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                            product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups(
                    'account.group_account_manager'):
                line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])

    def calculate_qty(self, today, num_of_month):
        qty = 0
        end_date = today + relativedelta(
            months=num_of_month, days=-1)
        num_of_month = (end_date.year - self.start_date.year) * 12 + (end_date.month - self.start_date.month)
        for i in range(0, num_of_month):
            if self.start_date and self.start_date < end_date:
                qty += 1
            else:
                qty = 1
        return qty

    def _prepare_invoice_line(self):
        vals = super(SaleOrderLine, self)._prepare_invoice_line()
        if not vals:
            return vals
        lang = self.order_id.partner_invoice_id.lang
        format_date = self.env['ir.qweb.field.date'].with_context(
            lang=lang).value_to_html
        today = fields.Date.today()
        if self.order_id.clx_invoice_policy_id:
            policy = self.order_id.clx_invoice_policy_id.policy_type
            if policy == 'advance':
                num_of_month = self.order_id.clx_invoice_policy_id.num_of_month + 1
                date_start = fields.Date.today().replace(day=1)
                date_end = date_start + relativedelta(months=num_of_month, days=-1)
                qty = self.calculate_qty(today, num_of_month)
                end_date = today + relativedelta(
                    months=num_of_month, days=-1)
                num_of_month = (end_date.year - self.start_date.year) * 12 + (end_date.month - self.start_date.month)
                period_msg = _("Invoicing period: %s - %s") % (
                    format_date(fields.Date.to_string(date_start), {}),
                    format_date(
                        fields.Date.to_string(date_end)
                        , {}
                    )
                )
                if num_of_month == 1:
                    period_msg = _("Invoicing period: %s - %s") % (
                        format_date(fields.Date.to_string(self.start_date), {}),
                        format_date(
                            fields.Date.to_string(date_end)
                            , {}
                        )
                    )
                vals.update({
                    'name': period_msg,
                    'quantity': qty
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
                    months=invoice_month + 1, days=-1) if not self.end_date else self.end_date
                current_month_start_date = date.today().replace(day=1)
                if current_month_start_date < self.start_date:
                    date_end = current_month_start_date + relativedelta(
                    months=invoice_month + 1, days=-1) if not self.end_date else self.end_date
            else:
                date_end = date_start + relativedelta(
                    months=invoice_month)
                date_end = date_end.replace(
                    day=monthrange(date_end.year, date_end.month)[1])
            if self.product_id.subscription_template_id.recurring_rule_type == 'yearly':
                date_end = date_start + relativedelta(
                    months=12, days=-1)

            res[0][-1].update({
                'invoice_start_date': date_start,
                'invoice_end_date': date_end,
            })
        return res
