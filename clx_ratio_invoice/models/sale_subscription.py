# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import api, fields, models


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    co_opp_partner_ids = fields.Many2many('co.op.sale.order.partner', string="Co-Opp Customers",
                                          compute="_compute_co_op_partner")

    def _compute_co_op_partner(self):
        for record in self:
            sale_lines = record.recurring_invoice_line_ids.mapped('so_line_id')
            sale_orders = sale_lines.mapped('order_id')
            if sale_orders:
                record.co_opp_partner_ids = sale_orders.co_op_sale_order_partner_ids.ids
            else:
                record.co_opp_partner_ids = False