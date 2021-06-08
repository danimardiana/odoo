# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import api, fields, models, _


class CoOpSaleOrderPartner(models.Model):
    _name = 'co.op.sale.order.partner'
    _description = "Co Op Sale Order"

    partner_id = fields.Many2one('res.partner', string='Customer')
    ratio = fields.Float(string="Ratio (%)")
    sale_order_line_id = fields.Many2one('sale.order.line', string='Sale Order')
