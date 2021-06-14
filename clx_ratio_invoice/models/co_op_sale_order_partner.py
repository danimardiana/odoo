# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CoOpSaleOrderPartner(models.Model):
    _name = "co.op.sale.order.partner"
    _description = "Co Op Sale Order"

    partner_id = fields.Many2one("res.partner", string="Customer",domain="[('company_type', '=', 'company')]")
    ratio = fields.Float(string="Ratio (%)")
    sale_order_line_id = fields.Many2one("sale.order.line", string="Sale Order")

    def unlink(self):
        try:
            form_view_id = self.env.ref("clx_ratio_invoice.co_op_saleorder_tree").id
        except Exception as e:
            form_view_id = False
        line_id = self.sale_order_line_id.id
        super(CoOpSaleOrderPartner, self).unlink()
        return {
            "type": "ir.actions.act_window",
            "name": "CO-OP companies list",
            # "view_type": "tree",
            # "view_mode": "tree",
            "res_model": "co.op.sale.order.partner",
            "views": [(form_view_id, "tree")],
            "domain": [("sale_order_line_id", "=", line_id)],
            "target": "new",
            "context": {"default_sale_order_line_id": line_id},
        }

    @api.onchange("ratio")
    def onchange_ratio(self):
        if not self.sale_order_line_id:
            return

        if self.ratio < 0:
            raise UserError(_("Percentage cant be negative !!"))
        related_lines = self.search(([("sale_order_line_id", "=", self.sale_order_line_id.id)]))

        ratio = self.ratio
        for line in related_lines:
            ratio += line.ratio
        if ratio > 100:
            raise UserError(_("You Can not add more than 100% !!"))


class CoOpSubscriptionPartner(models.Model):
    _name = "co.op.subscription.partner"
    _description = "Co Op Subscription"

    partner_id = fields.Many2one("res.partner", string="Customer", domain="[('company_type', '=', 'company')]")
    ratio = fields.Float(string="Ratio (%)")
    subscription_id = fields.Many2one("sale.subscription", string="Subscription")
