# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, models

contract_lengths_const = [
            ('1_m', '1 month'),('2_m', '2 months'),('3_m', '3 months'),
            ('4_m', '4 months'),('5_m', '5 months'),('6_m', '6 months'),
            ('7_m', '7 months'),('8_m', '8 months'),('9_m', '9 months'),
            ('10_m', '10 months'),('11_m', '11 months'),('12_m', '12 months'),
        ]
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    contract_length = fields.Selection(string="Contract Length",store=True,
        selection = contract_lengths_const, default='3_m')
    intended_launch_date = fields.Date(string='Intended Launch Date')
    setup_fee = fields.Char(string="Setup Fee")

    def get_text_contract_length(self):
        if not self.contract_length:
            return ''
        return dict(contract_lengths_const)[self.contract_length]

    def sale_order_email_action(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        self.ensure_one()
        template= self.env['mail.template'].sudo().search([('name','=','Sales Order: CLX email template')])
        lang = self.env.context.get('lang')
        template_id = template.id
        if template.lang:
            lang = template._render_template(template.lang, 'sale.order', self.ids[0])
        ctx = {            
            'tpl_partners_only': True,
            'default_model': 'sale.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            'model_description': self.with_context(lang=lang).type_name,
            'report_name':(self.name or '').replace('/','_')+'_000',
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