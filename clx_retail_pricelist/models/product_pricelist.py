# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    min_price = fields.Float("Min. Price")
    is_fixed = fields.Boolean('Fixed Price')
    is_percentage = fields.Boolean('Percentage')
    is_custom = fields.Boolean('Custom')
    is_wholesale_percentage = fields.Boolean('Percentage')
    is_wholesale_formula = fields.Boolean('Formula')
    fixed_mgmt_price = fields.Float('Fixed Price', digits='Product Price')
    percent_mgmt_price = fields.Float('Percentage Price')
    percent_wholesale_price = fields.Float('Percentage Price')
    min_retail_amount = fields.Float('Minimum Retail Amount')
    display_management_fee = fields.Boolean(
        string="Display Management Fee")

    @api.onchange('applied_on', 'product_id', 'product_tmpl_id', 'categ_id')
    def onchange_product_consistency(self):
        for item in self:
            if item.applied_on == '3_global':
                item.display_management_fee = True
            elif item.applied_on == '2_product_category' and item.categ_id.management_fee and item.categ_id.wholesale:
                item.display_management_fee = True
            elif item.applied_on == '1_product' and item.product_tmpl_id.categ_id.management_fee and item.categ_id.wholesale:
                item.display_management_fee = True
            elif item.applied_on == '0_product_variant' and item.product_id.categ_id.management_fee and item.categ_id.wholesale:
                item.display_management_fee = True
            else:
                item.display_management_fee = False

    @api.onchange('is_custom')
    def onchange_is_custom(self):
        if self.is_custom:
            self.is_fixed = True
            self.is_percentage = False

    @api.onchange('is_fixed')
    def onchange_is_fixed(self):
        if self.is_fixed:
            self.is_custom = False

    @api.onchange('is_percentage')
    def onchange_is_percentage(self):
        if self.is_percentage:
            self.is_custom = False

    @api.onchange('is_wholesale_percentage')
    def onchange_is_wholesale_percentage(self):
        if self.is_wholesale_percentage:
            self.is_wholesale_formula = False

    @api.onchange('is_wholesale_formula')
    def onchange_is_wholesale_formula(self):
        if self.is_wholesale_formula:
            self.is_wholesale_percentage = False
