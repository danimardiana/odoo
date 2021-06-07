# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, api, _

class AccountSendInvoice(models.TransientModel):
    _inherit = 'account.invoice.send'
    _description = 'account.invoice.send'

    def send_and_print_action(self):
        for rec in self.invoice_ids.filtered(lambda x: x.state not in ['cancel','email_sent'] ):
            rec.state = 'email_sent'
        res = super(AccountSendInvoice, self).send_and_print_action()
        return res