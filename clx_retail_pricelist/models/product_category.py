# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

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