# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.


from odoo import api, fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    pricing_type = fields.Selection(
        selection=[
            ('percentage_management_fee', '% based with management fee'),
            ('flat_cost_with_COG', 'Flat cost with a COG'),
            ('flat_cost', 'Flat cost')],
        string="Pricing Type")
    retail = fields.Boolean("Retail", default=True)
    wholesale = fields.Boolean("Wholesale")
    management_fee = fields.Boolean("Management Fee")

    @api.onchange('pricing_type')
    def onchange_pricing_type(self):
        """

        :return: None
        """
        if self.pricing_type:
            if self.pricing_type == 'percentage_management_fee':
                self.retail = True
                self.wholesale = True
                self.management_fee = True
            elif self.pricing_type == 'flat_cost_with_COG':
                self.retail = True
                self.wholesale = True
