# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import api, fields, models


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    display_management_fee = fields.Boolean(string='Display Management Fee')


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

    is_cat_mgt_fees = fields.Boolean(string='Categ Management')
    is_cat_wholesale = fields.Boolean(string='Categ Wholesale')
    min_price = fields.Float(string='Min. Price')

    is_fixed = fields.Boolean(string='Fixed Price')
    is_percentage = fields.Boolean(string='Percentage')
    is_custom = fields.Boolean(string='Custom')
    fixed_mgmt_price = fields.Float(string='Fixed Price',
                                    digits='Product Price')
    min_retail_amount = fields.Float(string='Minimum Retail Amount')
    percent_mgmt_price = fields.Float(string='Percentage')

    is_wholesale_percentage = fields.Boolean(string='Percentage')
    is_wholesale_formula = fields.Boolean(string='Formula')
    percent_wholesale_price = fields.Float(string='Percentage')

    @api.onchange('is_cat_mgt_fees')
    def onchange_is_cat_mgt_fees(self):
        """
        If is_cat_mgt_fees is not set then reset Management related fields
        :return: None
        """
        if not self.is_cat_mgt_fees:
            self.is_custom = self.is_percentage = self.is_fixed = False
            self.fixed_mgmt_price = \
                self.min_retail_amount = self.percent_mgmt_price = 0.0

    @api.onchange('is_cat_wholesale')
    def onchange_is_cat_wholesale(self):
        """
        If is_cat_wholesale is not set then reset Wholesale related fields
        :return: None
        """
        if not self.is_cat_wholesale:
            self.is_wholesale_percentage = self.is_wholesale_formula = False
            self.percent_wholesale_price = 0.0

    @api.onchange('applied_on', 'categ_id', 'product_tmpl_id', 'product_id')
    def onchange_applied_on(self):
        """
        To set booleans for is_cat_mgt_fees and is_cat_wholesale based on
        Applied On, Category, Product/Variant Category
        :return: None
        """
        self.is_cat_mgt_fees = self.is_cat_wholesale = False
        if self.applied_on == '3_global':
            self.is_cat_mgt_fees = self.is_cat_wholesale = True
        elif self.applied_on == '2_product_category' and self.categ_id:
            self.is_cat_mgt_fees = self.categ_id.management_fee
            self.is_cat_wholesale = self.categ_id.wholesale
        elif self.applied_on == '1_product' and \
                self.product_tmpl_id and self.product_tmpl_id.categ_id:
            categ = self.product_tmpl_id.categ_id
            self.is_cat_mgt_fees = categ.management_fee
            self.is_cat_wholesale = categ.wholesale
        elif self.applied_on == '0_product_variant' and \
                self.product_id and self.product_id.categ_id:
            self.is_cat_mgt_fees = self.product_id.categ_id.management_fee
            self.is_cat_wholesale = self.product_id.categ_id.wholesale

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
