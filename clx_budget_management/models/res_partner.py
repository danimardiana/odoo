# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def get_subscriptions(self):
        if self._context.get('se_order_id', False):
            sale_order_id = self._context.get('se_order_id', False)
            lines = self.env['sale.subscription.line'].search([
                ('so_line_id.order_id.partner_id', 'child_of', self.id),
                ('so_line_id.order_id', '=', sale_order_id),
            ])
            return lines
