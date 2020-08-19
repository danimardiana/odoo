# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    clx_invoice_policy_id = fields.Many2one(
        'clx.invoice.policy', string="Invoice Policy")

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(SaleOrder, self).onchange_partner_id()
        if self.partner_id:
            self.clx_invoice_policy_id = self.partner_id.clx_invoice_policy_id.id if \
                self.partner_id.clx_invoice_policy_id else False

    @api.model
    def create(self, vals):
        so = super(SaleOrder, self).create(vals)
        if so.partner_id:
            so.clx_invoice_policy_id = so.partner_id.clx_invoice_policy_id.id
        return so
