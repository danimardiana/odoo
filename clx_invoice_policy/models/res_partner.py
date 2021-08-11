# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from datetime import date

from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from odoo import fields, models, api, _
from calendar import monthrange

# from . import grouping_data

# products_set_grouping_level = grouping_data.products_set_grouping_level


class Partner(models.Model):
    _inherit = "res.partner"

    clx_invoice_policy_id = fields.Many2one("clx.invoice.policy", string="Invoice Policy")
    is_subscribed = fields.Boolean(string="Subscribed?", tracking=True, default=True)
    policy_hst_ids = fields.One2many("policy.history", "partner_id", string="Policy")
    invoice_selection = fields.Selection(
        [("prod_categ", "Product Category"), ("sol", "Sale Order Line")], string="Display on", default="sol"
    )

    invoice_creation_type = fields.Selection(
        [("combined", "Combined"), ("separate", "Separate")], string="Invoice Creation Type", default="separate"
    )

    child_invoice_selection = fields.Selection(
        related="management_company_type_id.invoice_selection", string="Display on"
    )
    is_generate_invoice = fields.Boolean(string="Is Generate Invoice?")

    def generate_invoice_with_date_range(self):
        view_id = self.env.ref("clx_invoice_policy.generate_invoice_date_range_form_view").id
        return {
            "type": "ir.actions.act_window",
            "name": _("Generate Invoice Date range"),
            "res_model": "generate.invoice.date.range",
            "target": "new",
            "view_mode": "form",
            "views": [[view_id, "form"]],
        }

    def generate_invoice(self):
        self.env["sale.subscription"].invoicing_invoice_policy_range(partner=self)

    # SB's invoice generation code. Could be removed as new inoicing code approved
    def get_advanced_sub_lines(self, lines):
        """
        To get all the lines which start in Advance month period.
        :param lines: Subscriptions lines
        :return: recordset after merge with advance services
        """
        ad_lines = self.env["sale.subscription.line"]
        today = date.today()
        for line in lines:
            policy_month = line.so_line_id.order_id.clx_invoice_policy_id.num_of_month
            end_date = today + relativedelta(months=policy_month + 1, days=-1)
            if line.invoice_start_date and line.invoice_start_date < end_date:
                ad_lines += line
        return ad_lines

    # remove when invoices moved
    def _merge_line_same_description(self, prepared_lines):
        base_lines = {}
        if prepared_lines:
            for line in prepared_lines:
                if line["description"] not in base_lines:
                    base_lines.update({line["description"]: line})
                else:
                    base_lines[line["description"]]["quantity"] = 1
                    base_lines[line["description"]]["price_unit"] += line["price_unit"]
                    base_lines[line["description"]]["tax_ids"][0][2].extend(line["tax_ids"][0][2])
                    base_lines[line["description"]]["analytic_account_id"] = line["analytic_account_id"]
                    base_lines[line["description"]]["analytic_tag_ids"][0][2].extend(line["analytic_tag_ids"][0][2])
                    # base_lines[line['description']]['subscription_ids'][0][2].extend(line['subscription_ids'][0][2])
                    # base_lines[line['description']]['subscription_lines_ids'].extend(line['subscription_lines_ids'])
        return base_lines

    def update_rebate_discount(self, draft_inv):
        """
        this method is used for the update rebate discount line value per invoice
        :param draft_inv: recordset of the account.move (draft invoice)
        :return:
        """
        discount_line = {}
        if draft_inv:
            for draft_invoice in draft_inv:
                receivable_line_debit = False
                total_discount = 0.0
                for inv_line in draft_invoice.invoice_line_ids.filtered(lambda x: "Rebate" not in x.name):
                    if self.management_company_type_id:
                        flat_discount = self.management_company_type_id.flat_discount
                        if (
                            self.management_company_type_id.is_flat_discount
                            and self.management_company_type_id.clx_category_id
                            and inv_line.category_id.id == self.management_company_type_id.clx_category_id.id
                        ):
                            total_discount += flat_discount
                        else:
                            total_discount += (
                                inv_line.price_unit * self.management_company_type_id.discount_on_order_line
                            ) / 100
                if total_discount:
                    rebate_line = draft_invoice.invoice_line_ids.filtered(lambda x: "Rebate" in x.name)
                    receivable_line = draft_invoice.line_ids.filtered(
                        lambda x: x.account_id.id == draft_invoice.partner_id.property_account_receivable_id.id
                    )
                    if rebate_line:
                        receivable_line_debit = rebate_line.debit
                        self.env.cr.execute("DELETE FROM account_move_line WHERE id = %s", (rebate_line.id,))
                    discount_line.update(
                        {
                            "price_unit": -abs(total_discount),
                            "category_id": False,
                            "product_uom_id": False,
                            "subscription_id": False,
                            #   'subscription_ids': False,
                            "sale_line_ids": False,
                            #   'subscription_lines_ids': False,
                            "name": "Rebate Discount",
                            "subscription_start_date": False,
                            "subscription_end_date": False,
                            "tax_ids": False,
                            "product_id": False,
                            "description": "Rebate Discount",
                        }
                    )
                    draft_invoice.with_context(check_move_validity=False, name="name").write(
                        {"invoice_line_ids": [(0, 0, discount_line)]}
                    )
                    if receivable_line:
                        receivable_line.debit += receivable_line_debit
                    # draft_invoice._onchange_recompute_dynamic_lines()
                    # draft_invoice._inverse_amount_total()

    def add_discount_line(self, invoice_line_ids):
        """
        add discount line in invoices
        :param invoice_line_ids: list of dictionary of invoice lines.
        :return: discount line (type Dictionary)
        """
        total_discount = 0.0
        discount_line = invoice_line_ids[0][-1].copy()
        for inv_val in invoice_line_ids:
            if self.management_company_type_id:
                flat_discount = self.management_company_type_id.flat_discount
                if (
                    self.management_company_type_id.is_flat_discount
                    and self.management_company_type_id.clx_category_id
                    and inv_val[-1]["category_id"] == self.management_company_type_id.clx_category_id.id
                ):
                    total_discount += flat_discount
                else:
                    total_discount += (
                        inv_val[-1]["price_unit"] * self.management_company_type_id.discount_on_order_line
                    ) / 100
        if total_discount:
            discount_line.update(
                {
                    "price_unit": -abs(total_discount),
                    "category_id": False,
                    "product_uom_id": False,
                    "subscription_id": False,
                    #   'subscription_ids': False,
                    "sale_line_ids": False,
                    #   'subscription_lines_ids': False,
                    "name": "Rebate Discount",
                    "subscription_start_date": False,
                    "subscription_end_date": False,
                    "tax_ids": False,
                    "product_id": False,
                    "description": "Rebate Discount",
                }
            )
            return discount_line

    def log_policy_history(self):
        """
        New history record will be created whenever user changes
        either Policy type or Subscribe/Unsubscribe
        :return: None
        """
        history = []
        for res in self:
            history.append(
                {
                    "partner_id": res.id,
                    "is_subscribed": res.is_subscribed,
                    "policy_type": res.clx_invoice_policy_id.policy_type,
                    "num_of_month": res.clx_invoice_policy_id.num_of_month,
                }
            )
        self.env["policy.history"].create(history)

    def subscription(self):
        """
        To subscribe and Unsubscribe.
        is_subscribed (Subscribed?) field is used to manage this operation
        :return: None
        """
        for res in self:
            res.is_subscribed = res.env.context.get("subscribe", False)
        self.log_policy_history()

    @api.model
    def create(self, vals):
        res = super(Partner, self).create(vals)
        if vals.get("clx_invoice_policy_id"):
            res.log_policy_history()
        return res

    def write(self, vals):
        res = super(Partner, self).write(vals)
        if vals.get("clx_invoice_policy_id"):
            self.log_policy_history()
        return res

    @api.model
    def _generate_subscription_invoices(self):
        """
        Scheduler Method: To generate invoice at the end of the month
        for those customers who subscribed and has Arrears policy
        :return: Boolean
        """
        customers = self.search(
            [
                ("is_subscribed", "=", True),
                ("active", "=", True),
                ("clx_invoice_policy_id", "!=", False),
                ("is_generate_invoice", "=", True),
            ],
            limit=50,
        )
        if not customers:
            return True
        try:
            for customer in customers:
                try:
                    customer.with_context(check_invoice_start_date=True).generate_invoice()
                    customer.is_generate_invoice = False
                except Exception as e:
                    print("-------Error at invoice creation------")
            return True
        except Exception as e:
            return False

    @api.model
    def _check_and_set_invoice_customers(self):
        customers = self.search([("is_subscribed", "=", True), ("clx_invoice_policy_id", "!=", False)])
        qry = """update res_partner set is_generate_invoice = True where id in %s"""
        self.env.cr.execute(qry, [tuple(customers.ids)])

    # not used now, can be deleted
    def new_generate_invoice(self):
        customers = self.search([("is_subscribed", "=", True), ("clx_invoice_policy_id", "!=", False)])
        # customers = self.browse(61427)
        if not customers:
            return True
        for customer in customers:
            start_date = fields.Date.today().replace(day=1)
            end_date = start_date + relativedelta(months=3)
            end_date = end_date + relativedelta(days=-1)
            lang = customer.lang
            format_date = self.env["ir.qweb.field.date"].with_context(lang=lang).value_to_html
            all_lines = self.env["sale.subscription.line"].search(
                [
                    ("so_line_id.order_id.partner_id", "child_of", customer.id),
                    ("so_line_id.order_id.state", "in", ("sale", "done")),
                ]
            )
            all_lines = all_lines.filtered(
                lambda sl: (
                    sl.so_line_id.order_id.clx_invoice_policy_id.policy_type == "advance"
                    and sl.product_id.subscription_template_id.recurring_rule_type == "monthly"
                )
            )
            count = len(
                OrderedDict(
                    ((start_date + timedelta(_)).strftime("%B-%Y"), 0) for _ in range((end_date - start_date).days)
                )
            )
            next_month_date = start_date
            start_date = start_date
            for i in range(0, count):
                next_month_date = next_month_date + relativedelta(months=1)
                end_date = date(start_date.year, start_date.month, monthrange(start_date.year, start_date.month)[-1])
                final_adv_line = self.env["sale.subscription.line"]

                for adv_line in all_lines:
                    if adv_line.product_id.subscription_template_id.recurring_rule_type == "monthly":
                        if not adv_line.end_date and end_date >= adv_line.start_date:
                            final_adv_line += adv_line
                        elif adv_line.end_date and adv_line.start_date <= end_date and start_date <= adv_line.end_date:
                            final_adv_line += adv_line
                advance_lines = final_adv_line
                period_msg = ("Invoicing period: %s - %s") % (
                    format_date(fields.Date.to_string(start_date), {}),
                    format_date(fields.Date.to_string(end_date), {}),
                )
                account_move_lines = self.env["account.move.line"].search(
                    [
                        ("partner_id", "=", customer.id),
                        ("name", "=", period_msg),
                        ("parent_state", "in", ("draft", "posted")),
                        ("subscription_lines_ids", "in", advance_lines.ids),
                    ]
                )
                if account_move_lines:
                    for ad_line in advance_lines:
                        if ad_line.id in account_move_lines.mapped("move_id").mapped("subscription_line_ids").ids:
                            advance_lines -= ad_line
                if customer.invoice_selection == "sol":
                    if sum(advance_lines.mapped("price_unit")) < 0:
                        downsell_lines = advance_lines.filtered(lambda x: x.line_type == "downsell")
                        if downsell_lines:
                            advance_lines -= downsell_lines
                            customer.with_context(
                                generate_invoice_date_range=True,
                                start_date=start_date,
                                end_date=end_date,
                                sol=True,
                            ).generate_advance_invoice(downsell_lines)
                    customer.with_context(
                        generate_invoice_date_range=True,
                        start_date=start_date,
                        end_date=end_date,
                        sol=True,
                    ).generate_advance_invoice(advance_lines)
                else:
                    if sum(advance_lines.mapped("price_unit")) < 0:
                        downsell_lines = advance_lines.filtered(lambda x: x.line_type == "downsell")
                        if downsell_lines:
                            advance_lines -= downsell_lines
                            customer.with_context(
                                generate_invoice_date_range=True,
                                start_date=start_date,
                                end_date=end_date,
                            ).generate_advance_invoice(downsell_lines)
                    customer.with_context(
                        generate_invoice_date_range=True,
                        start_date=start_date,
                        end_date=end_date,
                    ).generate_advance_invoice(advance_lines)

                for adv_line in all_lines:
                    if (
                        adv_line.product_id.subscription_template_id.recurring_rule_type == "yearly"
                        and adv_line.invoice_start_date == next_month_date
                    ):
                        advance_lines += adv_line
                    elif adv_line.product_id.subscription_template_id.recurring_rule_type == "yearly":
                        advance_lines -= adv_line
                start_date = start_date + relativedelta(months=1)

    # returning the array of contacts
    # Could be filtered by group_name: 'Billing Contact', 'Proofing Contact'...
    def contacts_to_notify(self, **kwargs):
        if "group_name" in kwargs:
            contacts = self.contact_child_ids.filtered(
                lambda contact: kwargs["group_name"] in contact.contact_type_ids.mapped("name")
            )
        else:
            contacts = self.contact_child_ids
        return contacts.mapped("child_id")

    @api.onchange("account_user_id")
    def _onchange_account_manager(self):
        partner_id = self.id or self.ids and self.ids[0]
        move_ids = self.env["account.move"].search([("partner_id", "=", partner_id), ("state", "!=", "cancel")])
        if move_ids:
            qry = """update account_move set invoice_user_id =""" + str(self.account_user_id.id) + """ where id in %s"""
            self.env.cr.execute(qry, [tuple(move_ids.ids)])