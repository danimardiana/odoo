# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    auto_add_main_task_ids = fields.Many2many('main.task', string="Parent Task")
