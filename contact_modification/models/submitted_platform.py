# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import api, fields, models


class SubmittedPlatform(models.Model):
    _name = 'submitted.platform'
    _description = 'Submitted Platform'

    name = fields.Char(string='Name')
