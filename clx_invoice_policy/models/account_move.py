# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, api, _
from dateutil import parser
from collections import OrderedDict
import datetime
from datetime import timedelta
import calendar
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = "account.move"

    mgmt_company = fields.Many2one(related="partner_id.management_company_type_id", store=True)

    subscription_line_ids = fields.Many2many("sale.subscription.line", "account_id", string="Subscription Lines")
    invoice_month_year = fields.Char(string="Invoicing Period")
    invoice_period_verbal = fields.Char(
        compute="compute_invoice_period_verbal", string="Invoice Period Verbal", store=False
    )
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('approved_draft', 'Approved Draft'),
        ('email_sent', 'Email Sent'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled')
    ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')
    related_contact_ids = fields.One2many(
        related="partner_id.contact_child_ids",
        string="Billing Contacts",
        store=False,
    )
    related_billing_contact_ids = fields.Many2many(
        "res.partner.clx.child", compute="compute_billing_contacts", string="Billing Contacts2", store=False
    )
    accounting_notes = fields.Text(string="Accounting Notes", compute="_compute_accounting_notes")
    unique_billing_note = fields.Boolean(string="Unique Billing Note")
    portable_invoice_url = fields.Char(string="Invoice link", index=True, compute="_compute_get_url")
    yardi_code = fields.Char(string="Yardi Code", related="partner_id.yardi_code")
    master_id = fields.Char(string="Master ID", related="partner_id.master_id")

    def _compute_get_url(self):
        for rec in self:
            host_url = self.env['ir.config_parameter'].get_param('web.base.url') or ''
            rec.portable_invoice_url = host_url + rec.get_portal_url() or ''

    @api.onchange('yardi_code')
    def _onchange_yardi_code(self):
        for rec in self:
            rec.partner_id.yardi_code = rec.yardi_code

    @api.onchange('master_id')
    def _onchange_master_id(self):
        for rec in self:
            rec.partner_id.master_id = rec.master_id

    @api.onchange('accounting_notes')
    def onchange_accounting_notes(self):
        self.partner_id.accounting_notes = self.accounting_notes

    def _compute_accounting_notes(self):
        self.accounting_notes = self.partner_id.accounting_notes

    def compute_billing_contacts(self):
        billing_list = map(
            lambda item: item.id,
            filter(
                lambda contact: "Billing Contact" in contact.contact_type_ids.mapped("name"), self.related_contact_ids
            ),
        )
        self.related_billing_contact_ids = [(6, 0, list(billing_list))]
    
    def post(self):
        res = super(AccountMove, self).post()
        sequence = self.env.ref("clx_invoice_policy.sequence_greystar_sequence")
        if (
            res
            and self.partner_id
            and self.partner_id.management_company_type_id
            and "Greystar" in self.partner_id.management_company_type_id.name
            and sequence
        ):
            self.name = sequence.next_by_code("greystar.sequence")
        return res

    @staticmethod
    def invoices_date_signature(date):
        return date.strftime("%Y-%m")

    def compute_invoice_period_verbal(self):
        for invoice in self:
            if invoice.invoice_month_year:
                year, month = invoice.invoice_month_year.split("-")
                # check for correct data
                if len(year) == 4 and len(month) == 2:
                    invoice.invoice_period_verbal = "%s %s" % (calendar.month_name[int(month)], year)
                    self.update_due_date()
                else:
                    invoice.invoice_period_verbal = "-"
            else:
                invoice.invoice_period_verbal = "-"

    def update_due_date(self):
        current_month = datetime.datetime.now().date().month
        current_year = datetime.datetime.now().date().year
        for invoice in self:
            new_val = invoice.invoice_month_year
            if new_val:
                year, month = new_val.split("-")
            if int(month) > current_month and int(year) >= current_year:
                invoice.invoice_date_due = datetime.date(int(year), int(month), 1)


    def unlink(self):
        for record in self:
            if record.invoice_origin:
                for inv_line in record.invoice_line_ids:
                    if inv_line.subscription_lines_ids:
                        name = inv_line.name.split(":")
                        name = name[-1].split("-")
                        start_date = parser.parse(name[0])
                        end_date = parser.parse(name[-1])
                        if start_date and end_date:
                            for sub in inv_line.subscription_lines_ids:
                                if not sub.end_date:
                                    sub.invoice_start_date = start_date.date()
                                    sub.invoice_end_date = end_date.date()
                                elif sub.end_date:
                                    month_count = len(
                                        OrderedDict(
                                            ((sub.end_date + timedelta(_)).strftime("%B-%Y"), 0)
                                            for _ in range((start_date.date() - sub.end_date).days)
                                        )
                                    )
                                    if month_count == 1 and start_date.date() > sub.end_date:
                                        sub.invoice_start_date = sub.start_date
                                        sub.invoice_end_date = sub.end_date
                                    elif sub.start_date > start_date.date():
                                        sub.invoice_start_date = sub.start_date
                                        sub.invoice_end_date = sub.end_date
                                    else:
                                        sub.invoice_start_date = start_date.date()
                                        sub.invoice_end_date = end_date.date()
        return super(AccountMove, self).unlink()

    def button_cancel(self):
        res = super(AccountMove, self).button_cancel()
        if self.invoice_origin:
            for inv_line in self.invoice_line_ids:
                if inv_line.subscription_lines_ids:
                    name = inv_line.name.split(":")
                    name = name[-1].split("-")
                    start_date = parser.parse(name[0])
                    end_date = parser.parse(name[-1])
                    if start_date and end_date:
                        for sub in inv_line.subscription_lines_ids:
                            if not sub.end_date:
                                sub.invoice_start_date = start_date.date()
                                sub.invoice_end_date = end_date.date()
                            elif sub.end_date:
                                month_count = len(
                                    OrderedDict(
                                        ((sub.end_date + timedelta(_)).strftime("%B-%Y"), 0)
                                        for _ in range((start_date.date() - sub.end_date).days)
                                    )
                                )
                                if month_count == 1 and start_date.date() > sub.end_date:
                                    sub.invoice_start_date = sub.start_date
                                    sub.invoice_end_date = sub.end_date
                                elif sub.start_date > start_date.date():
                                    sub.invoice_start_date = sub.start_date
                                    sub.invoice_end_date = sub.end_date
                                else:
                                    sub.invoice_start_date = start_date.date()
                                    sub.invoice_end_date = end_date.date()
        return res

    # rewriting the eamil sending function
    def action_invoice_sent(self, reminder=False):
        self.ensure_one()

        template = self.env["mail.template"].sudo().search([("name", "=", "Invoice: CLX email template")])
        template_id = template.id
        account_manager = self.partner_id.account_user_id.partner_id
        default_partner_ids = [account_manager.id] + self.partner_id.contacts_to_notify().mapped("id")
        contacts_billing = [account_manager.id] + self.partner_id.contacts_to_notify(group_name="Billing Contact").mapped("id")

        if template.lang:
            lang = template._render_template(template.lang, "account.move", self.ids[0])

        url = self.get_portal_url()

        if reminder:
            email_text = """ Attached is your recent invoice. Please review for dates of service and terms specific to your account.</p><p>To avoid interruption of your campaign(s) and/or other services such as Live Chat or The Conversion Cloud, we need to receive payment prior to the service date"""

        else:
            email_text = " To ensure your campaign runs as planned, please be reminded to ensure we receive payment by May 31, 2021. Payment in full is required to start or continue service. Attached is the invoice for your reference."

        ctx = {
            "tpl_partners_only": True,
            "default_model": "account.move",
            "default_res_id": self.ids[0],
            "default_use_template": bool(template_id),
            "default_template_id": template_id,
            "default_composition_mode": "comment",
            "default_partner_ids": contacts_billing,
            "default_email_to": "",
            "default_reply_to": "",
            "mark_so_as_sent": True,
            "custom_layout": "mail.mail_notification_paynow",
            "proforma": self.env.context.get("proforma", False),
            "force_email": True,
            "model_description": self.with_context(lang=lang).type_name,
            "report_name": (self.name or "").replace("/", "_") + "_000",
            "default_allowed_partner_ids": default_partner_ids,
            "secure_url": url,
            "email_text": email_text,
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

    def action_reminder_sent(self):
        return self.action_invoice_sent(True)

    # no status for mail sending
    def email_send_postprocess(self):
        return
      
    def button_approve_invoice(self):
        for rec in self.filtered(lambda x: x.state == 'draft'):
            rec.state = 'approved_draft'

    @api.model_create_multi
    def create(self, vals_list):
        res = super(AccountMove, self).create(vals_list)
        #Updating invoice user id as it's partner's account manager
        if res.partner_id and res.partner_id.account_user_id:
            res.invoice_user_id = res.partner_id.account_user_id
        res.update_due_date()
        return res

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    category_id = fields.Many2one("product.category", string="Category")
    subscription_ids = fields.Many2many("sale.subscription", string="Subscription(s)")
    subscription_lines_ids = fields.Many2many("sale.subscription.line", string="Subscriptions Lines")

    management_fees = fields.Float(string="Management Fees")
    retail_price = fields.Float(string="Retails Price")
    wholesale = fields.Float(string="Wholsesale")
    description = fields.Char(string="Description")
