# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models

class ResCompany(models.Model):
    _inherit = "res.company"

    routing_number = fields.Char(string='Routing Number')

