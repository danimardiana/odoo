# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def get_subscriptions(self):
        lines = self.env['sale.subscription.line'].search([
            ('so_line_id.order_id.partner_id', 'child_of', self.id),
            ('so_line_id.order_id.state', 'in', ('sale', 'done')),
        ])
        return lines
