# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from datetime import date
from collections import OrderedDict
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_invoiced = fields.Boolean(string='invoiced')
    prorate_amount = fields.Float(string="One-Time Amount")

    @api.onchange('product_id')
    def onchange_start_date(self):
        if self.product_id and self.order_id.contract_start_date:
            self.start_date = self.order_id.contract_start_date
        elif self.product_id and not self.start_date:
            raise ValidationError(_("Please select start date."))

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
                end_date = today + relativedelta(months=num_of_month, days=-1)
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
        base_line = self.subscription_id.recurring_invoice_line_ids.filtered(lambda x: x.line_type == 'base')
        if self.order_id and self.order_id.clx_invoice_policy_id and \
                self.order_id.clx_invoice_policy_id.policy_type == 'advance':
            date_start = self.start_date
            invoice_month = self.order_id.clx_invoice_policy_id and \
                            self.order_id.clx_invoice_policy_id.num_of_month + 1
            if self.order_id.partner_id.invoice_creation_type == 'separate':
                invoice_month = 1
            if self.line_type == 'base':
                date_start = date_start.replace(day=1)
                date_end = date_start + relativedelta(
                    months=invoice_month, days=-1) if not self.end_date else self.end_date
            else:
                date_end = date_start + relativedelta(
                    months=invoice_month, days=-1) if not self.end_date else self.end_date
            month_count = len(OrderedDict(((self.start_date + timedelta(_)).strftime("%B-%Y"), 0) for _ in
                                          range((date_end - self.start_date).days)))
            if month_count > 1:
                date_end = date_start + relativedelta(
                    months=invoice_month, days=-1)
            elif month_count == 1 and self.line_type != 'base':
                date_end = date_start + relativedelta(
                    months=invoice_month, days=-1) if not self.end_date else self.end_date
            if self.product_id.subscription_template_id.recurring_rule_type == 'yearly':
                date_end = date_start + relativedelta(
                    months=12, days=-1)
            res[0][-1].update({
                'invoice_start_date': self.start_date,
                'invoice_end_date': date_end,
                'name': base_line[0].name if base_line else self.name
            })
        return res

    @staticmethod
    def _grouping_by_product_logic(product, partner, line_name):
        if product.name != line_name:
            description = line_name
        else:
            description = product.name
            if partner.vertical in ("res", "srl") and product.budget_wrapping:
                description = product.budget_wrapping
            else:
                if product.budget_wrapping_auto_local:
                    description = product.budget_wrapping_auto_local
        return description

    def _grouping_name_calc(self, line):
        description = line.product_id.categ_id.name
        partner_id = line.order_id.partner_id
        product_id = line.product_id
        if partner_id.invoice_selection == "sol":
            description = self._grouping_by_product_logic(product_id, partner_id, line.name)

        return description