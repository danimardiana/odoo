# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _action_confirm(self):
        result = super(SaleOrder, self)._action_confirm()
        for line in self.order_line:
            if line.task_id and not line.task_id.clx_sale_order_id and not line.task_id.clx_sale_order_line_id:
                line.task_id.write(
                    {
                        'clx_sale_order_id': line.order_id.id,
                        'clx_sale_order_line_id': line.id
                    }
                )
            if line.project_id and not line.project_id.clx_sale_order_id:
                line.project_id.write({
                    'clx_sale_order_id': line.order_id.id
                })
        return result
