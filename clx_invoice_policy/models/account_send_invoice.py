# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, api, _

class AccountSendInvoice(models.TransientModel):
    _inherit = 'account.invoice.send'
    _description = 'account.invoice.send'

    def send_and_print_action(self):
        # the email_sent state could be set for "posted" invoices only
        for rec in self.invoice_ids.filtered(lambda x: x.state in ['posted']):
            rec.state = 'email_sent'
        res = super(AccountSendInvoice, self).send_and_print_action()
        return res

    @api.model
    def default_get(self, fields):
        res = super(AccountSendInvoice, self).default_get(fields)
        if not res.get('allowed_partner_ids'):
            res['allowed_partner_ids'] = self.get_allowed_ids().ids
        if not res.get('partner_ids') and res.get('allowed_partner_ids'):
            res['partner_ids'] = self.with_context(type_name='Billing Contact').get_allowed_ids().ids
        return res

    def get_allowed_ids(self):
        move_ids = self.env["account.move"].browse(self._context.get('active_ids', self.res_id))
        if self._context.get('type_name'):

            contacts = move_ids.mapped('partner_id')
            return contacts.mapped('account_user_id').mapped('partner_id') + contacts.contacts_to_notify(
                group_name=self._context.get('type_name'))
        partner_ids = move_ids.mapped('partner_id').contacts_to_notify()
        self.allowed_partner_ids = partner_ids
        return partner_ids

    allowed_partner_ids = fields.One2many("res.partner", compute="get_allowed_ids", string="List of contacts")


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    @api.model
    def _message_get_default_recipients_on_records(self, records):
        res = super(MailThread, self)._message_get_default_recipients_on_records(records)
        if records and records[0]._context.get('active_model') == 'account.move':
            res = {}
            for record in records:
                recipient_ids, email_to, email_cc = [], False, False
                if 'partner_id' in record and record.partner_id:
                    partner_ids = record.partner_id.account_user_id.partner_id + \
                                  record.partner_id.contacts_to_notify(group_name='Billing Contact')
                    recipient_ids.append(partner_ids.ids)
                elif 'email_normalized' in record and record.email_normalized:
                    email_to = record.email_normalized
                elif 'email_from' in record and record.email_from:
                    email_to = record.email_from
                elif 'partner_email' in record and record.partner_email:
                    email_to = record.partner_email
                elif 'email' in record and record.email:
                    email_to = record.email
                res[record.id] = {'partner_ids': recipient_ids, 'email_to': email_to, 'email_cc': email_cc}
        return res


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    def get_mail_values(self, res_ids):
        res = super(MailComposer, self).get_mail_values(res_ids)
        try:
            if self._context.get('active_model') == 'account.move':
                move_ids = self.env['account.move'].browse(res_ids)
                for move in move_ids:
                    res[move.id]['recipient_ids'] = []
                    partner_ids = move.partner_id.account_user_id.partner_id + \
                                  move.partner_id.contacts_to_notify(group_name='Billing Contact')
                    for partner in partner_ids:
                        res[move.id]['recipient_ids'].append((4, partner.id))
        except Exception as e:
            pass
        return res