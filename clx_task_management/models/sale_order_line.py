# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, models, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    project_id = fields.Many2one('project.project', string="Project")
    task_id = fields.Many2one('project.task', string='Task')
    is_qty_readonly = fields.Boolean('product.category', related="product_id.categ_id.is_qty_readonly")

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        res = super(SaleOrderLine, self).product_uom_change()
        if self.order_id.pricelist_id and self.product_id:
            item_ids = self.order_id.pricelist_id.item_ids
            item = item_ids.filtered(lambda x: (x.product_tmpl_id.id == self.product_id.product_tmpl_id.id)
                                               or
                                               (x.categ_id.id == self.product_id.categ_id.id)
                                               or
                                               (x.product_id.id == self.product_id.id)
                                     )
            if item:
                self.price_unit = item[0].min_price
            if not item:
                return res
