# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class SaleOrder(models.Model):
    _inherit = "sale.order"
    is_co_op = fields.Boolean(string="Co-op opt in")


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    co_op_sale_order_line_partner_ids = fields.One2many(
        "co.op.sale.order.partner", "sale_order_line_id", string="CO-OP Customers"
    )
    total_coop_percenage = fields.Float(compute="calculate_total_coop_percenage", store=False, string="co-op %")
    is_co_op = fields.Boolean(related="order_id.is_co_op", store=False)

    # tree view open to add the coop companies to sales order line
    def sale_order_line_action(self):
        try:
            form_view_id = self.env.ref("clx_ratio_invoice.co_op_saleorder_tree").id
        except Exception as e:
            form_view_id = False
        return {
            "type": "ir.actions.act_window",
            "name": "CO-OP companies list",
            # "view_type": "tree",
            # "view_mode": "tree",
            "res_model": "co.op.sale.order.partner",
            "views": [(form_view_id, "tree")],
            "domain": [("sale_order_line_id", "=", self.id)],
            "target": "new",
            "context": {"default_sale_order_line_id": self.id},
        }

    @api.model
    def calculate_total_coop_percenage(self):
        for line in self:
            line.total_coop_percenage = sum(line.co_op_sale_order_line_partner_ids.mapped("ratio"))

    # @api.onchange('is_ratio')
    # def onchange_is_ratio(self):
    #     co_op = self.env['co.op.sale.order.partner']
    #     if self.partner_id:
    #         vals = {
    #             'partner_id': self.partner_id.id
    #         }
    #         co_op_partner_id = co_op.create(vals)
    #         self.co_op_sale_order_partner_ids = [(6, 0, co_op_partner_id.ids)]