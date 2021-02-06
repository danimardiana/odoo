# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    state_ids = fields.Many2many('res.country.state', string="States")
    category_ids = fields.Many2many('product.category', string="Category")
