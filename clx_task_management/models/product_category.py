# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    is_qty_readonly = fields.Boolean(string='Is Quantity Readonly?')
