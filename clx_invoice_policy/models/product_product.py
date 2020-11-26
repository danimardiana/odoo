# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    budget_wrapping = fields.Char(string="Budget Wrapping for AUTO/LOCAL")

    # def name_get(self):
    #     if not self.env.context.get('hierarchical_naming', True):
    #         return [(record.id, record.name) for record in self]
    #     return super(ProductProduct, self).name_get()
