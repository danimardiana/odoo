# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    setup_fees = fields.Float(string="Setup Fees")
