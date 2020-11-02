# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_ratio = fields.Boolean('Co - Op')
    co_op_sale_order_partner_ids = fields.One2many('co.op.sale.order.partner', 'sale_order_id', string="Co op Customer")

    @api.onchange('co_op_sale_order_partner_ids')
    def onchange_co_op_sale_order_partner_ids(self):
        ratio = 0
        for line in self.co_op_sale_order_partner_ids:
            ratio += line.ratio
        if ratio > 100:
            raise UserError(_("You Can not add more than 100% !!"))

    @api.onchange('is_ratio')
    def onchange_is_ratio(self):
        co_op = self.env['co.op.sale.order.partner']
        if self.partner_id:
            vals = {
                'partner_id': self.partner_id.id
            }
            co_op_partner_id = co_op.create(vals)
            self.co_op_sale_order_partner_ids = [(6, 0, co_op_partner_id.ids)]
