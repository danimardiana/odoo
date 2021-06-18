# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import api, fields, models


class LeadManagementSystem(models.Model):
    _name = "lead.management.system"
    _description = "Lead Management System"

    name = fields.Char(string="Name")
