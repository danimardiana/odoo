# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    partner_id = fields.Many2one(
        'res.partner', string='Vendor',
        required=True, states=READONLY_STATES,
        change_default=True, tracking=True,
        domain="["
               "('company_type','=','vendor'),"
               "('company_id', 'in', [company_id, False])]",
        help="You can find a vendor by its Name, TIN, Email "
             "or Internal Reference.")
