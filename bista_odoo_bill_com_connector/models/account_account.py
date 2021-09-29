# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountAccount(models.Model):
    _inherit = 'account.account'

    bill_com_coa_id = fields.Char('Bill.com ID', copy=False)

    