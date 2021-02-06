# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import models, api


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _compute_tax_id(self):
        for line in self:
            fpos = line.order_id.fiscal_position_id or line.order_id.partner_id.property_account_position_id
            # If company_id is set in the order, always filter taxes by the company
            taxes = line.product_id.taxes_id.filtered(lambda r: r.company_id == line.order_id.company_id)
            tax = self.env['account.tax'].search(
                [('state_ids', 'in', self.order_id.partner_id.state_id.id),
                 ('category_ids', 'in', self.product_id.categ_id.id)], limit=1)
            if tax:
                line.tax_id = tax.ids
            else:
                line.tax_id = fpos.map_tax(taxes, line.product_id, line.order_id.partner_shipping_id) if fpos else taxes