# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    contract_length = fields.Char(string="Contract Length")
    intended_launch_date = fields.Date(string='Intended Launch Date')
    setup_fee = fields.Char(string="Setup Fee")
