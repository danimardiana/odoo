# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, api, _
from dateutil import parser
from collections import OrderedDict
from datetime import timedelta
import calendar


class AccountMove(models.Model):
    _inherit = "account.move.invoice.line"
    _description = "Invoice Lines as they will be reflected on the invoce"

    move_id = fields.Many2one('account.move', string='Journal Entry',
        index=True, required=True, readonly=True, auto_join=True, ondelete="cascade",
        help="The move of this entry line.")
    price_unit = fields.Float(string='Unit Price', digits='Product Price')
    partner_id = fields.Many2one('res.partner', string='Partner', ondelete='restrict')
    product_id = fields.Many2one('product.product', string='Product')
    price_total = fields.Monetary(string='Total', store=True, readonly=True,
        currency_field='always_set_currency_id')
    description = fields.Char(string="Description")