# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import api, fields, models


class ProductPricelistItem(models.Model):
    """
    Product Pricelist Item inherited to set
    - Management Price Computation
    - Wholesale Price Computation
    Fixed Price: To set Flat Management Fees Applicable
        ( Ex. - $1000 Fixed)
    Percentage: To set Management Fess as % of Retail Price
        ( Ex. - 20% of Retail)
    Custom: To set the condition based Management Fees
        (Ex. - 15% of Retail if Minimum Retails Price is $4000 or above
    """
    _inherit = 'product.pricelist.item'

    is_cat_mgt_fees = fields.Boolean(related='categ_id.management_fee')
    is_cat_wholesale = fields.Boolean(related='categ_id.wholesale')

    is_fixed = fields.Boolean(string='Fixed Price')
    is_percentage = fields.Boolean(string='Percentage')
    is_custom = fields.Boolean(string='Custom')
    fixed_mgmt_price = fields.Float(string='Fixed Price',
                                    digits='Product Price')
    min_retail_amount = fields.Float(string='Minimum Retail Amount')
    percent_mgmt_price = fields.Float(string='Percentage')

    is_wholesale_percentage = fields.Boolean(string='Percentage')
    is_wholesale_formula = fields.Boolean(string='Formula')
    min_price = fields.Float(string='Min. Price')
    percent_wholesale_price = fields.Float(string='Percentage')

    @api.onchange('is_custom')
    def onchange_is_custom(self):
        """
        Custom to set minimum retail amount
        With fix amount
        :return: None
        """
        if self.is_custom:
            self.is_fixed = True

    @api.onchange('is_wholesale_percentage')
    def onchange_is_wholesale_percentage(self):
        """
        To calculate wholesale with percentage
        :return: None
        """
        if self.is_wholesale_percentage:
            self.is_wholesale_formula = False

    @api.onchange('is_wholesale_formula')
    def onchange_is_wholesale_formula(self):
        """
        To calculate wholesale with formula
        :return: None
        """
        if self.is_wholesale_formula:
            self.is_wholesale_percentage = False
