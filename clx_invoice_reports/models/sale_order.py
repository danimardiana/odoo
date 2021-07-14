# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo.tools.mail import email_send
from odoo import fields, models, api
import json

contract_lengths_const = [
    ("1_m", "1 month"),
    ("2_m", "2 months"),
    ("3_m", "3 months"),
    ("4_m", "4 months"),
    ("5_m", "5 months"),
    ("6_m", "6 months"),
    ("7_m", "7 months"),
    ("8_m", "8 months"),
    ("9_m", "9 months"),
    ("10_m", "10 months"),
    ("11_m", "11 months"),
    ("12_m", "12 months"),
]


class SaleOrder(models.Model):
    _inherit = "sale.order"

    contract_length = fields.Selection(
        string="Contract Length", store=True, selection=contract_lengths_const, default="1_m"
    )
    intended_launch_date = fields.Date(string="Intended Launch Date")
    setup_fee = fields.Char(string="Setup Fee")
    mail_compose_message_id = fields.Many2many("mail.compose.message", string="List of templates")

    def get_text_contract_length(self):
        if not self.contract_length:
            return ""
        return dict(contract_lengths_const)[self.contract_length]

    def sale_order_email_action(self):
        """ Opens a wizard to compose an email, with relevant mail template loaded by default """
        self.ensure_one()
        template = self.env["mail.template"].sudo().search([("name", "=", "Sales Order: CLX email template")])
        lang = self.env.context.get("lang")
        template_id = template.id
        account_manager = self.partner_id.account_user_id.partner_id

        contacts_billing = [account_manager.id] + self.partner_id.contacts_to_notify().mapped("id")

        if template.lang:
            lang = template._render_template(template.lang, "sale.order", self.ids[0])
        secure_url = self._get_share_url(redirect=True, signup_partner=True)
        ctx = {
            "tpl_partners_only": True,
            "default_model": "sale.order",
            "default_res_id": self.ids[0],
            "default_use_template": bool(template_id),
            "default_template_id": template_id,
            "default_composition_mode": "comment",
            "default_partner_ids": [account_manager.id],
            "default_email_to": "",
            "default_reply_to": "",
            "mark_so_as_sent": True,
            "custom_layout": "mail.mail_notification_paynow",
            "proforma": self.env.context.get("proforma", False),
            "force_email": True,
            "model_description": self.with_context(lang=lang).type_name,
            "report_name": (self.name or "").replace("/", "_") + "_000",
            "default_allowed_partner_ids": contacts_billing,
            "secure_url": secure_url,
        }
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(False, "form")],
            "view_id": False,
            "target": "new",
            "context": ctx,
        }

    # overwriting the confirmation email sending function
    def _send_order_confirmation_mail(self):
        self.ensure_one()
        template = self.env["mail.template"].sudo().search([("name", "=", "Contract: Signing confirmation")])
        # getting the previous mail to send confirmation to the same addresses
        previous_mail_array = (
            self.env["mail.compose.message"].sudo().search([("res_id", "=", self.id)], order="id desc")
        )

        # as previous emails will have one recepient only we have to collect them all
        lang = self.env.context.get("lang")
        ctx = {
            "tpl_partners_only": True,
            "default_model": "sale.order",
            "default_res_id": self.ids[0],
            "default_use_template": bool(template.id),
            "default_template_id": template.id,
            "default_composition_mode": "comment",
            # "default_partner_ids": previous_mail_array[0].partner_ids,
            # "default_email_to": previous_mail_array[0].email_to,
            # "default_reply_to": previous_mail_array[0].reply_to,
            # "default_subject": previous_mail_array[0].subject,
            "mark_so_as_sent": True,
            "custom_layout": "mail.mail_notification_light",
            "proforma": self.env.context.get("proforma", False),
            "force_email": True,
            "model_description": self.with_context(lang=lang).type_name,
            "report_name": (self.name or "").replace("/", "_") + "_000",
            "force_send": True,
        }

        # Create the composer
        composer = self.env["mail.compose.message"].with_context(ctx).create({})
        update_values = composer.onchange_template_id(template.id, "comment", self._name, self.ids[0])["value"]
        composer.write(update_values)

        if template.id:
            body_html = template._render_template(template.body_html, "sale.order", self.id, post_process=False)
            subject = template._render_template(template.subject, "sale.order", self.id, post_process=False)
            email_from = template._render_template(template.email_from, "sale.order", self.id, post_process=False)
            all_recepients = []
            for previous_mail in previous_mail_array:
                if previous_mail.partner_ids:
                    all_recepients += previous_mail.partner_ids.mapped("email")

                if type(previous_mail.email_to) is str:
                    all_recepients += previous_mail.email_to.split(",")

            # Account Manager mandratory
            all_recepients += [self.partner_id.account_user_id.email]

            # removing duplicates
            all_recepients = list(dict.fromkeys(all_recepients))

            for recipient in all_recepients:
                prepeared_values = {
                    "email_to": recipient,
                    "body_html": body_html,
                    "attachment_ids": [attach.id for attach in composer.attachment_ids],
                    "subject": subject,
                    "email_from": email_from,
                    "reply_to":email_from,
                }
                Mail = self.env["mail.mail"].create(prepeared_values)
                Mail.send()

    def email_send_postprocess(self):
        self.state = "sent"