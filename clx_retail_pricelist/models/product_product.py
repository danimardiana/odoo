# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    contract_product_description = fields.Text(
        string="Description for the Product as it will appear in contract")
