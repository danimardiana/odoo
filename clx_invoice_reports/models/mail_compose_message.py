# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, models, api
import json


class MaleComposeMessage(models.TransientModel):
    _inherit = "mail.compose.message"

    def get_allowed_ids(self):
        if not self.allowed_partner_ids_storage:
            return False
        ids_process = self.env["res.partner"].search([("id", "in", json.loads(self.allowed_partner_ids_storage))])
        self.allowed_partner_ids = ids_process

    def set_allowed_ids(self):
        self.allowed_partner_ids_storage = json.dumps(list(map(lambda x: x.id, self.allowed_partner_ids)))

    email_to = fields.Char(string="Additional e-mails")
    allowed_partner_ids = fields.One2many(
        "res.partner", compute="get_allowed_ids", inverse="set_allowed_ids", string="List of contacts"
    )
    allowed_partner_ids_storage = fields.Char(string="List of contacts in JSON")

    def clx_action_send_mail(self):
        prepeared_values = {
            # 'email_to': self.email_to,
            "body_html": self.body,
            "attachment_ids": self.attachment_ids,
            "recipient_ids": False,  # self.partner_ids,
            "subject": self.subject,
            "email_from": self.email_from,
            "reply_to": self.reply_to,
        }
        array_of_recipients = []
        if type(self.email_to) is str:
            array_of_recipients += self.email_to.split(",")

        if self.partner_ids:
            array_of_recipients += self.partner_ids.mapped("email")

        for recipient in array_of_recipients:
            prepeared_values["email_to"] = recipient.strip()
            Mail = self.env["mail.mail"].create(prepeared_values)
            object_source = self.env[self.model].browse(self.res_id)
            object_source.email_send_postprocess();
            Mail.send()

        invoice_ids = self.env["account.move"].browse(self._context.get("active_ids", []))
        for rec in invoice_ids:
            rec.state = "invoice_sent"

        return {"type": "ir.actions.act_window_close", "infos": "mail_sent"}
