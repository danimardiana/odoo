# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, models, api
import json


class MaleComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def get_allowed_ids(self):
        if not self.allowed_partner_ids_storage:
            return False
        ids_process = self.env['res.partner'].search(
            [('id', 'in', json.loads(self.allowed_partner_ids_storage))])
        self.allowed_partner_ids = ids_process

    def set_allowed_ids(self):
        self.allowed_partner_ids_storage = json.dumps(
            list(map(lambda x: x.id, self.allowed_partner_ids)))

    email_to = fields.Char(string="Additional e-mails")
    allowed_partner_ids = fields.One2many(
        'res.partner', compute='get_allowed_ids', inverse='set_allowed_ids', string="List of contacts")
    allowed_partner_ids_storage = fields.Char(
        string="List of contacts in JSON")

    def action_send_mail_sales_order(self):
        prepeared_values = {
            'email_to': self.email_to,
            'body_html': self.body,
            'attachment_ids': self.attachment_ids,
            'recipient_ids': self.partner_ids,
            'subject': self.subject,
            'email_from': self.email_from,
        }
        Mail = self.env['mail.mail'].create(prepeared_values)
        Mail.send()
        return {'type': 'ir.actions.act_window_close', 'infos': 'mail_sent'}
