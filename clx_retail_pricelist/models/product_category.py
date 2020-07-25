# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import api, fields, models


class ProductCategory(models.Model):
    """
    Product Category Inherited to set Retail, Wholesale and Management changes
    """
    _inherit = 'product.category'

    pricing_type = fields.Selection([
        ('percentage_management_fee', '% based with management fee'),
        ('flat_cost_with_COG', 'Flat cost with a COG'),
        ('flat_cost', 'Flat cost')
    ], string='Pricing Type')
    retail = fields.Boolean(string='Retail', default=True)
    wholesale = fields.Boolean(string='Wholesale')
    management_fee = fields.Boolean(string='Management Fee')

    @api.onchange('pricing_type')
    def onchange_pricing_type(self):
        """
        Retail, Wholesale and Management Fees boolean must be set as per type
        % based with management fee:
        Flat cost with a COG:
        Flat cost:
        :return: None
        """
        if not self.pricing_type or self.pricing_type == 'flat_cost':
            self.retail = True
            self.wholesale = False
            self.management_fee = False
        elif self.pricing_type == 'percentage_management_fee':
            self.retail = True
            self.wholesale = True
            self.management_fee = True
        elif self.pricing_type == 'flat_cost_with_COG':
            self.retail = True
            self.wholesale = True
            self.management_fee = False
