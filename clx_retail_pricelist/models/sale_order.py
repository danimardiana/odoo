# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class ProductPriceCalculation(models.Model):
    _name = "product.price.calculation"

    product_id = fields.Many2one('product.product', string="Product")
    management_fees = fields.Float("Management Fees")
    retail_fees = fields.Float("Retail fees")
    wholesale = fields.Float("Wholesale")
    order_id = fields.Many2one('sale.order')


class SaleOrder(models.Model):
    _inherit = "sale.order"

    product_price_calculation_ids = fields.One2many(
		'product.price.calculation',
		'order_id',
		readonly=True,
		string="Product Price")