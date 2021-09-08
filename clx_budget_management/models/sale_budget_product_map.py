# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
# Description: This table contain the product pairs should be treated same on the 
# Budget Change algorythm

from odoo import fields, models


class SaleBudgetProductMap(models.Model):
    _name = "sale.budget.product.map"
    _description = "Product Mapping"

    product_1_id = fields.Many2one("product.product", string="Product 1")
    product_2_id = fields.Many2one("product.product", string="Product 2")
