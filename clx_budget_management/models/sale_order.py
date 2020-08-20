# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _action_confirm(self):
        """
        inherited method for create budget line when confirm the sale order
        """
        res = super(SaleOrder, self)._action_confirm()
        self.env['sale.subscription']._create_sale_budget(self)
        return res
