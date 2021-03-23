# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, models

contract_lengths_const = [
            ('1_m', '1 month'),('2_m', '2 months'),('3_m', '3 months'),
            ('4_m', '4 months'),('5_m', '5 months'),('6_m', '6 months'),
            ('7_m', '7 months'),('8_m', '8 months'),('9_m', '9 months'),
            ('10_m', '10 months'),('11_m', '11 months'),('12_m', '12 months'),
        ]
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    contract_length = fields.Selection(string="Contract Length",store=True,
        selection = contract_lengths_const, default='3_m')
    intended_launch_date = fields.Date(string='Intended Launch Date')
    setup_fee = fields.Char(string="Setup Fee")

    def _get_text_contract_length(self):
        return dict(contract_lengths_const)[self.contract_length]
