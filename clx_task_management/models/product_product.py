# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_task_create = fields.Boolean(string="Generate Task", default=True)
