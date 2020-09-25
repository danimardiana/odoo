# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    project_id = fields.Many2one('project.project', string="Project")
    task_id = fields.Many2one('project.task', string='Task')
    is_qty_readonly = fields.Boolean('product.category', related="product_id.categ_id.is_qty_readonly")
