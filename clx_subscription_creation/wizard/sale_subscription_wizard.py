# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo.exceptions import ValidationError

from odoo import models, fields, api, _


class SaleSubscriptionWizard(models.TransientModel):
    _inherit = "sale.subscription.wizard"

    end_date = fields.Date(string="End Date")

    @api.onchange("date_from", "end_date")
    def onchange_date_validation(self):
        if self.date_from and self.end_date and self.date_from >= self.end_date:
            raise ValidationError(_("Invalid date range."))

    @api.model
    def default_get(self, fields):
        res = super(SaleSubscriptionWizard, self).default_get(fields)
        subscription = self.env.context["active_id"]
        subscription_id = self.env["sale.subscription"].browse(subscription)
        product_id = subscription_id.sudo().recurring_invoice_line_ids[-1].product_id
        if subscription_id and subscription_id.recurring_invoice_line_ids and product_id:
            res["option_lines"] = [
                (
                    0,
                    0,
                    {
                        "product_id": product_id.id,
                        "uom_id": product_id.uom_id.id,
                        "name": product_id.description if product_id.description else product_id.name,
                    },
                )
            ]
        return res

    def create_sale_order(self):
        """
        inherit this method because of set start date from sale subscription wizard to sale order
        """
        res = super(SaleSubscriptionWizard, self).create_sale_order()
        if self.option_lines[0].price == 0:
            raise ValidationError(_("Please add Upsell Price!!"))
        active_subscription = self.env["sale.subscription"].browse(self._context.get("active_id"))
        order_id = active_subscription.recurring_invoice_line_ids[0].mapped("so_line_id").order_id
        res_id = res.get("res_id", False)
        wholesale = 0.0
        management_fees = 0.0
        if res_id:
            so = self.env["sale.order"].browse(res_id)
            so.onchange_partner_id()
            if order_id:
                so.clx_invoice_policy_id = order_id[0].clx_invoice_policy_id.id
                so.contract_start_date = order_id[0].contract_start_date
            so.start_date = self.date_from if self.date_from else False
            sol_id = so.order_line.filtered(lambda x: x.product_id.id == self.option_lines[0].product_id.id)
            is_co_op = False
            if sol_id:
                price_list = so.pricelist_id
                base_line = active_subscription.recurring_invoice_line_ids.filtered(lambda x: x.line_type == "base")
                price_unit = active_subscription.recurring_total + self.option_lines[0].price
                if price_list:
                    rule = price_list[0].item_ids.filtered(lambda x: x.categ_id.id == sol_id.product_id.categ_id.id)
                price = self.option_lines[0].price
                sol_id.write(
                    {
                        "price_unit": price,
                        "product_uom_qty": 1,
                        "start_date": self.date_from,
                        "end_date": self.end_date,
                        "name": base_line and base_line[0].name,
                        "discount": 0.0,
                        "line_type": "downsell" if price < 0 else "upsell",
                    }
                )
                # copy proration from  the source subscription
                if len(active_subscription.co_op_partner_ids):
                    is_co_op = True
                    for line in active_subscription.co_op_partner_ids:
                        coop_object = {
                            "partner_id": line.partner_id.id,
                            "ratio": line.ratio,
                            "sale_order_line_id": sol_id.id,
                        }
                        self.env["co.op.sale.order.partner"].create(coop_object)
                # sol_id.price_unit_change()
                # so.update_price()
                # so.is_ratio = order_id.is_ratio
                # if order_id.is_ratio:
                #     so.co_op_sale_order_partner_ids = order_id.co_op_sale_order_partner_ids.ids
                so.is_co_op = is_co_op
                so.action_confirm()
        return res


class SaleSubscriptionWizardOption(models.TransientModel):
    _inherit = "sale.subscription.wizard.option"

    price = fields.Float(string="Price")