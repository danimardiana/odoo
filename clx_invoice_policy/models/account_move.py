# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from datetime import date
from dateutil.relativedelta import relativedelta
import datetime

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
    account_user_id = fields.Many2one("res.users", string="Account Manager")
    secondary_user_id = fields.Many2one("res.users", string="Secondary Acct. Manager")
    national_user_id = fields.Many2one("res.users", string="National Acct. Manager")

    post_date = fields.Date(string="Invoice Post Date")

    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("approved_draft", "Approved Draft"),
            ("posted", "Posted"),
            ("email_sent", "Email Sent"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default="draft",
    )

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
    is_co_op = fields.Boolean(string="Invoice Contains CO-OP Subscriptions", readonly=True)
    yardi_code = fields.Char(string="Yardi Code", related="partner_id.yardi_code")
    master_id = fields.Char(string="Master ID", related="partner_id.master_id")

    # overwriting the preview invoice logic
    def client_invoice_grouping(self):
        # sub_lines = self.subscription_line_ids
        # # grouping flags = 7, means use all groupings
        # year, month = year, day = self.invoice_month_year.split("-")
        # start_date = date(int(year), int(month), 1)
        # end_date = start_date + relativedelta(months=1, days=-1)
        # partner_id = self.partner_id
        # # invoice generation flow. Should do all kinds of grouping
        # grouped_lines = self.env["sale.subscription"]._grouping_wrapper(
        #     start_date=start_date, partner_id=partner_id, subscripion_line=sub_lines, grouping_levels=7
        # )

        # for line in grouped_lines.values():
        #     line["price_subtotal"] = line["price_unit"]
        #     line["price_total"] = line["price_unit"]

        # return list(grouped_lines.values())
        return self.invoice_line_ids

    def _compute_get_url(self):
        for rec in self:
            host_url = self.env["ir.config_parameter"].get_param("web.base.url") or ""
            rec.portable_invoice_url = host_url + rec.get_portal_url() or ""

    @api.onchange("yardi_code")
    def _onchange_yardi_code(self):
        for rec in self:
            rec.partner_id.yardi_code = rec.yardi_code

    @api.onchange("master_id")
    def _onchange_master_id(self):
        for rec in self:
            rec.partner_id.master_id = rec.master_id

    @api.onchange("accounting_notes")
    def onchange_accounting_notes(self):
        self.partner_id.accounting_notes = self.accounting_notes

    def _compute_accounting_notes(self):
        for move in self:
            move.accounting_notes = move.partner_id.accounting_notes

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
        self.post_date = datetime.datetime.now()
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
                else:
                    invoice.invoice_period_verbal = "-"
            else:
                invoice.invoice_period_verbal = "-"

    @api.onchange("invoice_month_year")
    def _onchange_invoice_month_year(self):
        self.update_due_date()

    @api.onchange("partner_id")
    def _onchange_partner(self):
        # update Analytic account based on partner vertical
        analytic_account_id = self.env["account.analytic.account"].search(
            [("vertical", "=", self.partner_id.vertical)], limit=1
        )
        if self.invoice_line_ids:
            self.invoice_line_ids.analytic_account_id = self.partner_id.vertical and analytic_account_id or False
            for line in self.invoice_line_ids:
                line.analytic_account_id = self.partner_id.vertical and analytic_account_id or line.analytic_account_id

    def update_due_date(self):
        current_month = datetime.datetime.now().date().month
        current_year = datetime.datetime.now().date().year
        for invoice in self:
            new_val = invoice.invoice_month_year
            if new_val:
                year, month = new_val.split("-")
                if int(month) > current_month and int(year) >= current_year:
                    invoice.invoice_date_due = datetime.date(int(year), int(month), 1) - datetime.timedelta(days=1)

    # rewriting the email sending function
    def action_invoice_sent(self, reminder=False):
        self.ensure_one()

        template = self.env["mail.template"].sudo().search([("name", "=", "Invoice: CLX email template")])
        template_id = template.id
        account_manager = self.partner_id.account_user_id.partner_id
        default_partner_ids = [account_manager.id] + self.partner_id.contacts_to_notify().mapped("id")
        contacts_billing = [account_manager.id] + self.partner_id.contacts_to_notify(
            group_name="Billing Contact"
        ).mapped("id")

        if template.lang:
            lang = template._render_template(template.lang, "account.move", self.ids[0])

        url = self.get_portal_url()

        if reminder:
            email_text = """ Attached is your recent invoice. Please review for dates of service and terms specific to your account.</p><p>To avoid interruption of your campaign(s) and/or other services such as Live Chat or The Conversion Cloud, we need to receive payment prior to the service date"""

        else:
            email_text = " To ensure your campaign runs as planned, please be reminded to ensure we receive payment by May 31, 2021. Payment in full is required to start or continue service. Attached is the invoice for your reference."

        invoice_lines_regrouped = []

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
        for rec in self.filtered(lambda x: x.state == "draft"):
            rec.state = "approved_draft"

    @api.model_create_multi
    def create(self, vals_list):
        res = super(AccountMove, self).create(vals_list)
        # updating Analytic account value if applicable
        res._onchange_partner()
        # Updating invoice user id as it's partner's account manager
        if res.partner_id:
            if res.partner_id.account_user_id:
                res.account_user_id = res.partner_id.account_user_id
            if res.partner_id.secondary_user_id:
                res.secondary_user_id = res.partner_id.secondary_user_id
            if res.partner_id.national_user_id:
                res.national_user_id = res.partner_id.national_user_id
        res.update_due_date()
        for move_id in res:
            if move_id.type == "out_invoice":
                current_month = datetime.datetime.now().month
                current_year = datetime.datetime.now().year
                new_val = move_id.invoice_month_year
                if new_val:
                    year, month = new_val.split("-")
                    if int(month) <= current_month and int(year) <= current_year:
                        for line in move_id.line_ids:
                            account = (
                                line.product_id.property_account_income_id
                                or line.product_id.categ_id.property_account_income_categ_id
                            )
                            line.account_id = account and account.id or line.account_id.id
        return res

    def _auto_create_asset(self):
        model_ids = []
        move = self and self[0]
        if move and move.is_invoice():
            model_ids = move.line_ids.account_id and move.line_ids.account_id.asset_model
        if model_ids:
            return super(AccountMove, self)._auto_create_asset()
        else:
            create_list = []
            invoice_list = []
            auto_validate = []
            for move in self:
                if not move.is_invoice():
                    continue
                for move_line in move.line_ids:
                    # and not move.reversed_entry_id -- removed condition
                    # it'll allow all the future invoices to create deferred revenue
                    if (
                        move_line.account_id
                        and (move_line.account_id.can_create_asset)
                        and move_line.account_id.create_asset != "no"
                        and not (move_line.currency_id or move.currency_id).is_zero(move_line.price_total)
                        and not move_line.asset_id
                    ):
                        if not move_line.name:
                            raise UserError(
                                _(
                                    "Journal Items of {account} should have a label in order to generate an asset"
                                ).format(account=move_line.account_id.display_name)
                            )
                        # Create first_depreciation_date
                        relative_date = datetime.date.today()
                        new_val = move.invoice_month_year
                        if new_val:
                            year, month = new_val.split("-")
                            if month.isdigit() and year.isdigit():
                                relative_date = relative_date.replace(day=1, month=int(month), year=int(year))
                        next_date = relative_date
                        dep_account_id = (
                            move_line.product_id.property_account_income_id.id
                            or move_line.product_id.categ_id.property_account_income_categ_id.id
                        )
                        vals = {
                            "name": move_line.name,
                            "company_id": move_line.company_id.id,
                            "currency_id": move_line.company_currency_id.id,
                            "account_depreciation_id": dep_account_id,
                            "account_depreciation_expense_id": move_line.account_id and move_line.account_id.id,
                            "original_move_line_ids": [(6, False, move_line.ids)],
                            "state": "draft",
                            "first_depreciation_date": next_date,
                        }
                        model_id = move_line.account_id.asset_model
                        if model_id:
                            vals.update(
                                {
                                    "model_id": model_id.id,
                                }
                            )
                        auto_validate.append(move_line.account_id.create_asset == "validate")
                        invoice_list.append(move)
                        create_list.append(vals)

            assets = self.env["account.asset"].create(create_list)
            # assets.update({'state':'draft'})
            for asset, vals, invoice, validate in zip(assets, create_list, invoice_list, auto_validate):

                asset._onchange_model_id()
                asset._onchange_method_period()
                if validate:
                    asset.validate()
                if invoice:
                    asset_name = {
                        "purchase": _("Asset"),
                        "sale": _("Deferred revenue"),
                        "expense": _("Deferred expense"),
                    }[asset.asset_type]
                    msg = _("%s created from invoice") % (asset_name)
                    msg += ": <a href=# data-oe-model=account.move data-oe-id=%d>%s</a>" % (invoice.id, invoice.name)
                    asset.message_post(body=msg)
            return assets


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    category_id = fields.Many2one("product.category", string="Category")
    description = fields.Char(string="Description")

    @api.onchange("tax_ids")
    def onchange_tax_ids(self):
        # prevent user to add tax on rebate products
        for line in self:
            if line.product_id == line.move_id.partner_id.management_company_type_id.discount_product:
                line.tax_ids = False
