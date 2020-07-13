# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    is_management_fee = fields.Boolean("Is Management Fee")
    min_price = fields.Float("Min. Price")
    compute_management_price = fields.Selection([
        ('fixed', 'Fixed Price'),
        ('percentage', 'Percentage (discount)')],
        index=True, default='fixed', required=False)
    fixed_manag_price = fields.Float('Fixed Price', digits='Product Price')
    percent_manag_price = fields.Float('Percentage Price')