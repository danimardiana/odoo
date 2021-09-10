# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # This function is overrided because wanted to make a relation based on the Vendor Reference.
    @api.depends('order_line.invoice_lines.move_id', 'order_line.invoice_lines.move_id.ref', 'partner_ref')
    def _compute_invoice(self):
        account_move_obj = self.env['account.move']
        for order in self:
            invoices = order.mapped('order_line.invoice_lines.move_id')
            partner_ref = order.partner_ref
            if partner_ref:
                cr = order._cr
                cr.execute("""SELECT id from account_move move where move.ref='%s' and move.partner_id=%s""" % (partner_ref, order.partner_id.id))
                invoice_exists = list(filter(None, map(lambda x: x[0], cr.fetchall())))
                if invoice_exists:
                    invoices |= account_move_obj.sudo().browse(invoice_exists)
            order.invoice_ids = invoices
            order.invoice_count = len(invoices)    