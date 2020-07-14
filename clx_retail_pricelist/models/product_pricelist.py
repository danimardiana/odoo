# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    is_management_fee = fields.Boolean("Is Management Fee")
    min_price = fields.Float("Min. Price")
    is_fixed = fields.Boolean('Fixed Price')
    is_percentage = fields.Boolean('Percentage')
    is_custom = fields.Boolean('Custom')
    fixed_mgmt_price = fields.Float('Fixed Price', digits='Product Price')
    percent_mgmt_price = fields.Float('Percentage Price')
    min_retail_amount = fields.Float('Minimum Retail Amount')

    @api.onchange('is_custom')
    def onchange_is_custom(self):
        if self.is_custom:
            self.is_fixed = False
            self.is_percentage = False

    @api.onchange('is_fixed')
    def onchange_is_fixed(self):
        if self.is_fixed:
            self.is_custom = False

    @api.onchange('is_percentage')
    def onchange_is_percentage(self):
        if self.is_percentage:
            self.is_custom = False
