# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    category_id = fields.Many2one('product.category', string="Category")
    subscription_ids = fields.Many2many(
        'account.move.line', string="Subscription(s)")
