# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo.exceptions import ValidationError

from odoo import models, fields, api, _


class SaleSubscriptionWizard(models.TransientModel):
    _inherit = 'sale.subscription.wizard'

    end_date = fields.Date(string="End Date")

    @api.onchange('date_from', 'end_date')
    def onchange_date_validation(self):
        if self.date_from and self.end_date and \
                self.date_from >= self.end_date:
            raise ValidationError(_("Invalid date range."))

    @api.model
    def default_get(self, fields):
        res = super(SaleSubscriptionWizard, self).default_get(fields)
        subscription = self.env.context['active_id']
        subscription_id = self.env['sale.subscription'].browse(subscription)
        product_id = subscription_id.sudo().recurring_invoice_line_ids[-1].product_id
        if subscription_id and subscription_id.recurring_invoice_line_ids and product_id:
            res['option_lines'] = [(0, 0, {
                'product_id': product_id.id,
                'uom_id': product_id.uom_id.id,
                'name': product_id.description if product_id.description else product_id.name,
            })]
        return res

    def create_sale_order(self):
        """
        inherit this method because of set start date from sale subscription wizard to sale order
        """
        res = super(SaleSubscriptionWizard, self).create_sale_order()
        if self.option_lines[0].price == 0:
            raise ValidationError(_("Please add Upsell Price!!"))
        active_subscription = self.env['sale.subscription'].browse(self._context.get('active_id'))
        order_id = active_subscription.recurring_invoice_line_ids[0].mapped('so_line_id').order_id
        res_id = res.get('res_id', False)
        wholesale = 0.0
        if res_id:
            so = self.env['sale.order'].browse(res_id)
            so.onchange_partner_id()
            if order_id:
                so.clx_invoice_policy_id = order_id[0].clx_invoice_policy_id.id
                so.contract_start_date = order_id[0].contract_start_date
            so.start_date = self.date_from if self.date_from else False
            sol_id = so.order_line.filtered(
                lambda x: x.product_id.id == self.option_lines[0].product_id.id)
            if sol_id:
                price_list = so.pricelist_id
                base_line = active_subscription.recurring_invoice_line_ids.filtered(lambda x: x.line_type == 'base')
                price_unit = active_subscription.recurring_total + self.option_lines[0].price
                if price_list:
                    rule = price_list[0].item_ids.filtered(
                        lambda x: x.categ_id.id == sol_id.product_id.categ_id.id)
                    if rule:
                        percentage_management_price = custom_management_price = 0.0
                        if rule.is_percentage:
                            percentage_management_price = price_unit * (
                                    (rule.percent_mgmt_price or 0.0) / 100.0)
                        if rule.is_custom and price_unit > rule.min_retail_amount:
                            custom_management_price = price_unit * (
                                    (rule.percent_mgmt_price or 0.0) / 100.0)
                        management_fees = max(percentage_management_price,
                                              custom_management_price,
                                              rule.fixed_mgmt_price)
                        if rule.is_wholesale_percentage:
                            wholesale = price_unit * (
                                    (rule.percent_wholesale_price or 0.0) / 100.0)
                        if rule.is_wholesale_formula:
                            wholesale = price_unit - management_fees
                price = self.option_lines[0].price
                sol_id.write({
                    'price_unit': price,
                    'product_uom_qty': 1,
                    'start_date': self.date_from,
                    'end_date': self.end_date,
                    'name': base_line and base_line[0].name,
                    'discount': 0.0,
                    'line_type': 'downsell' if price < 0 else 'upsell',
                    'management_price': management_fees - sum(active_subscription.recurring_invoice_line_ids.mapped(
                        'management_price')) if management_fees < sum(
                        active_subscription.recurring_invoice_line_ids.mapped('management_price')) else abs(
                        management_fees - sum(
                            active_subscription.recurring_invoice_line_ids.mapped('management_price'))),
                    'wholesale_price': abs(
                        wholesale - sum(active_subscription.recurring_invoice_line_ids.mapped(
                            'wholesale_price'))) if price > 0 else wholesale - sum(
                        active_subscription.recurring_invoice_line_ids.mapped(
                            'wholesale_price'))
                })
                # sol_id.price_unit_change()
                # so.update_price()
                so.action_confirm()
        return res


class SaleSubscriptionWizardOption(models.TransientModel):
    _inherit = "sale.subscription.wizard.option"

    price = fields.Float(string="Price")
