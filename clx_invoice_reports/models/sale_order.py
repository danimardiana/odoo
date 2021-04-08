# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, models, api
import json

contract_lengths_const = [
    ('1_m', '1 month'), ('2_m', '2 months'), ('3_m', '3 months'),
    ('4_m', '4 months'), ('5_m', '5 months'), ('6_m', '6 months'),
    ('7_m', '7 months'), ('8_m', '8 months'), ('9_m', '9 months'),
    ('10_m', '10 months'), ('11_m', '11 months'), ('12_m', '12 months'),
]


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    contract_length = fields.Selection(string="Contract Length", store=True,
                                       selection=contract_lengths_const, default='1_m')
    intended_launch_date = fields.Date(string='Intended Launch Date')
    setup_fee = fields.Char(string="Setup Fee")
    mail_compose_message_id = fields.Many2many(
        'mail.compose.message',  string="List of templates")

    def get_text_contract_length(self):
        if not self.contract_length:
            return ''
        return dict(contract_lengths_const)[self.contract_length]

    def sale_order_email_action(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        self.ensure_one()
        template = self.env['mail.template'].sudo().search(
            [('name', '=', 'Sales Order: CLX email template')])
        lang = self.env.context.get('lang')
        template_id = template.id
        contacts_billing = []
        for contact in self.partner_id.contact_child_ids:
            contacts_billing.append(contact.child_id.id)
        account_manager = self.partner_id.account_user_id.partner_id
        contacts_billing.append(account_manager.id)
        if template.lang:
            lang = template._render_template(
                template.lang, 'sale.order', self.ids[0])
        secure_url = self._get_share_url(redirect=True, signup_partner=True)
        ctx = {
            'tpl_partners_only': True,
            'default_model': 'sale.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'default_partner_ids': [account_manager.id],
            'default_email_to': '',
            'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            'model_description': self.with_context(lang=lang).type_name,
            'report_name': (self.name or '').replace('/', '_')+'_000',
            'default_allowed_partner_ids': contacts_billing,
            'secure_url': secure_url,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    # overwriting the confirmation email sending function
    def _send_order_confirmation_mail(self):
        self.ensure_one()
        template = self.env['mail.template'].sudo().search(
            [('name', '=', 'Contract: Signing confirmation')])
        # getting the previous mail to send confirmation to the same addresses
        previous_mail = self.env['mail.compose.message'].sudo().search(
            [('res_id', '=', self.id)], limit=1, order='id desc')[0]
        lang = self.env.context.get('lang')
        ctx = {
            'tpl_par    tners_only': True,
            'default_model': 'sale.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template.id),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
            'default_partner_ids': previous_mail.partner_ids,
            'default_email_to': previous_mail.email_to,
            'default_subject': previous_mail.subject,
            'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_light",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            'model_description': self.with_context(lang=lang).type_name,
            'report_name': (self.name or '').replace('/', '_')+'_000',
            'force_send': True,
        }
        
        # return
        if template.id:
            #generate composition using the mail template
            compose = self.with_context(ctx).message_post_with_template(
                template.id, composition_mode='comment', email_layout_xmlid="mail.mail_notification_light")
            # prepeared_values = {
            #     'email_to': compose.email_to,
            #     'body_html': compose.body,
            #     'attachment_ids': compose.attachment_ids,
            #     'recipient_ids': compose.partner_ids,
            #     'subject': compose.subject,
            #     'email_from': compose.email_from,
            # }
            # Mail = self.env['mail.mail'].create(prepeared_values)
        
