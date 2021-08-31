# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from itertools import product
from dateutil import parser
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
from datetime import timedelta, date
from odoo.exceptions import ValidationError, UserError
from odoo import fields, models, api, _
import calendar
from . import grouping_data

INVOICE_LINE_MESSAGE_TEMPLATE = "Invoicing period: %s - %s"


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    clx_invoice_policy_id = fields.Many2one("clx.invoice.policy", string="Invoice Policy")

    def _compute_invoice_count(self):
        invoice = self.env["account.move"]
        can_read = invoice.check_access_rights("read", raise_exception=False)
        for subscription in self:
            subscription.invoice_count = (
                can_read
                and invoice.search_count(
                    [
                        # "|",
                        # ("invoice_line_ids.subscription_id", "=", subscription.id),
                        ("subscription_line_ids", "in", subscription.id),
                    ]
                )
                or 0
            )

    def action_subscription_invoice(self):
        self.ensure_one()
        invoices = self.env["account.move"].search(
            [
                # "|",
                # ("invoice_line_ids.subscription_id", "in", self.ids),
                ("subscription_line_ids", "in", self.id),
            ]
        )
        action = self.env.ref("account.action_move_out_invoice_type").read()[0]
        action["context"] = {"create": False}
        if len(invoices) > 1:
            action["domain"] = [("id", "in", invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref("account.view_move_form").id, "form")]
            if "views" in action:
                action["views"] = form_view + [(state, view) for state, view in action["views"] if view != "form"]
            else:
                action["views"] = form_view
            action["res_id"] = invoices.ids[0]
        else:
            action = {"type": "ir.actions.act_window_close"}
        return action

    def pricelist_determination(self, product, price_list):
        pricelist_flat = self.pricelist_flatten(price_list)
        pricelist2process = False
        tags = [
            str(price_list.id) + "_0_" + str(product.id),
            str(price_list.id) + "_1_" + str(0 if "product_tmpl_id" not in product else product.product_tmpl_id.id),
            str(price_list.id) + "_2_" + str(product.categ_id.id),
            str(price_list.id) + "_3",
            # list(pricelist_flat.keys())[0], not need to assign any pricelist
        ]
        for tag in tags:
            if tag in pricelist_flat:
                pricelist2process = pricelist_flat[tag]
                break
        return pricelist2process

    def subscription_wholesale_period(
        self, retail, price_list, show_flags={"show_mgmnt_fee": True, "show_wholesale": True}
    ):

        if not price_list or not price_list.active:
            return {
                "management_fee": -2,
                "wholesale_price": -2,
                "management_fee_product": False,
            }

        if retail == 0:
            return {"management_fee": 0, "wholesale_price": 0}

        management_fee = 0.0 if show_flags["show_mgmnt_fee"] else False
        wholesale = 0.0 if show_flags["show_wholesale"] else False
        management_fee_product = (
            None if "management_fee_product" not in price_list else price_list.management_fee_product
        )

        if price_list.is_custom and management_fee == 0.0:
            if retail <= price_list.min_retail_amount:
                management_fee = price_list.fixed_mgmt_price
            else:
                management_fee = round((price_list.percent_mgmt_price * retail) / 100, 2)
        else:
            # if management fee fixed
            if (
                price_list.is_fixed
                and price_list.fixed_mgmt_price
                and show_flags["show_mgmnt_fee"]
                and retail > price_list.fixed_mgmt_price
            ):
                management_fee = price_list.fixed_mgmt_price

            # if management fee percentage
            if price_list.is_percentage and price_list.percent_mgmt_price and show_flags["show_mgmnt_fee"]:
                management_fee = round((price_list.percent_mgmt_price * retail) / 100, 2)

            # if wholesale fee percentage
            if (
                price_list.is_wholesale_percentage
                and price_list.percent_wholesale_price
                and show_flags["show_wholesale"]
            ):
                wholesale = round((price_list.percent_wholesale_price * retail) / 100, 2)

        # but never less than minimum price
        if management_fee < price_list.fixed_mgmt_price:
            management_fee = price_list.fixed_mgmt_price

        if wholesale == 0.0:
            wholesale = retail - management_fee

        return {
            "management_fee": management_fee if management_fee else -1,
            "wholesale_price": wholesale if wholesale else -1,
            "management_fee_product": management_fee_product,
        }

    def pricelist_flatten(self, price_list):
        mapped = {}

        def prod_var(price_line):
            return str(price_list.id) + "_0_" + str(price_line.product_id.id)

        def prod(price_line):
            return str(price_list.id) + "_1_" + str(price_line.product_tmpl_id.id)

        def category(price_line):
            return str(price_list.id) + "_2_" + str(price_line.categ_id.id)

        def glob(price_line):
            return str(price_list.id) + "_3"

        pricelistLevels = {
            "0_product_variant": prod_var,
            "1_product": prod,
            "2_product_category": category,
            "3_global": glob,
        }

        for price_line in price_list.item_ids:
            tag = pricelistLevels[price_line.applied_on](price_line)
            mapped[tag] = price_line

        return mapped

    # check if subscription was invoiced for period (using invoice_month_year signature)
    # product = False when we are looking for ANY invoice for client
    def are_invoices_for_period(self, partner_id, date, states=False, product=False):
        invoice_object = self.env["account.move"]
        period_msg = invoice_object.invoices_date_signature(date)
        all_filters = [
            ("invoice_month_year", "=", period_msg),
            ("partner_id.id", "=", partner_id),
        ]

        if states:
            all_filters.append(("state", "in", states))

        if product and "id" in product:
            all_filters.append(("subscription_line_ids.id", "=", product.id))

        all_draft_invoices = invoice_object.search(all_filters)
        return all_draft_invoices or False

    # generating invoice basing on the datarange
    def format_period_message(self, start_date, end_date):
        format_date = self.env["ir.qweb.field.date"].value_to_html
        return (INVOICE_LINE_MESSAGE_TEMPLATE) % (
            format_date(fields.Date.to_string(start_date), {}),
            format_date(fields.Date.to_string(end_date), {}),
        )

    def invoicing_date_range(self, **kwargs):
        today = date.today()

        if "start_date" in kwargs:
            start_date = kwargs["start_date"].replace(day=1)
        else:
            start_date = today

        if "partner" not in kwargs and "partner_id" in kwargs:
            partner = self.env["res.partner"].browse(kwargs["partner_id"])
        else:
            partner = kwargs["partner"]

        # if no ending dates in parameters just take the same month
        if "end_date" in kwargs:
            end_date = kwargs["end_date"].replace(day=1) + relativedelta(months=1, days=-1)
        else:
            end_date = start_date + relativedelta(months=1, days=-1)

        difference_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
        parameters = kwargs.copy()
        results = []
        for current_month in range(difference_months):
            end_date_period = start_date + relativedelta(months=1, days=-1)
            parameters.update({"start_date": start_date, "end_date": end_date_period})
            results.append(self.invoicing_one_period(**parameters))
            start_date += relativedelta(months=1)

        return results

    # invoicing client for Invoice Policy period
    # TODO: finish
    def invoicing_invoice_policy_range(self, **kwargs):
        today = date.today()

        if "start_date" in kwargs:
            start_date = kwargs["start_date"].replace(day=1)
        else:
            start_date = today.replace(day=1)

        if "partner_id" not in kwargs:
            kwargs.update({"partner_id": kwargs["partner"].id})

        if kwargs["partner"].clx_invoice_policy_id:
            end_date = date.today() + relativedelta(months=kwargs["partner"].clx_invoice_policy_id.num_of_month + 1)
        else:
            end_date = start_date + relativedelta(months=1, days=-1)

        kwargs.update({"end_date": end_date, "start_date": start_date})

        return self.invoicing_date_range(**kwargs)

    # generates invoice for one period
    def invoicing_one_period(self, **kwargs):
        if (
            (("partner_id" not in kwargs) and ("order_id" not in kwargs))
            or ("start_date" not in kwargs)
            or ("end_date" not in kwargs)
        ):
            return False

        order_id = kwargs["order_id"] if "order_id" in kwargs else False

        partner_id = kwargs["partner_id"]

        partner = self.env["res.partner"].browse(partner_id)

        # get all subscription lines
        lines = self.subscription_lines_collection_for_invoicing(
            partner, order_id, kwargs["start_date"], kwargs["end_date"], grouping_data.DESCRIPTION_GROUPING_FLAG
        )
        # not create invoices if no lines to invoice or all have 0
        if (
            not lines
            or not lines["related_subscriptions"]
            or not (any(list(map(lambda l: l["price_unit"], lines["invoice_lines"]))))
        ):
            return False

        is_co_op = any(
            list(
                map(
                    lambda l: (
                        l.analytic_account_id.co_op_partner_ids and len(l.analytic_account_id.co_op_partner_ids) > 0
                    ),
                    lines["related_subscriptions"],
                )
            )
        )

        last_order = sorted(
            lines["related_subscriptions"], key=lambda kv: kv.so_line_id.order_id.create_date, reverse=True
        )[0].so_line_id.order_id
        # generating the new invoice
        invoice_origin = {}
        for line in lines["related_subscriptions"]:
            invoice_origin[line.so_line_id.order_id.name] = True

        invoice_signature = self.env["account.move"].invoices_date_signature(kwargs["start_date"])
        total_invoice_value = sum(map(lambda line: line.price_unit, lines["related_subscriptions"]))
        posted_invoice = self.env["account.move"].search(
            [
                ("partner_id", "=", partner_id),
                ("state", "in", ("email_sent", "posted")),
                ("invoice_month_year", "=", invoice_signature),
            ],
            limit=1,
        )

        # if total negative - create the credit note. Prepearing the variables
        if total_invoice_value < 0:
            # reverting valaues
            for line in lines["invoice_lines"]:
                line["price_unit"] = -line["price_unit"]
                line["price_subtotal"] = -line["price_subtotal"]

            invoice_type_settings = {
                "ref": "Credit note",
                "type": "out_refund",
                "reversed_entry_id": posted_invoice.id,
            }
        else:
            invoice_type_settings = {
                "ref": "Invoice",
                "type": "out_invoice",
                "reversed_entry_id": posted_invoice.id,
            }

        if "draft_invoice" in lines:
            # updating the draft invoice
            invoice = self.env["account.move"].browse(lines["draft_invoice"])
            invoice_included_subscription_ids = list(map(lambda line: line.id, lines["related_subscriptions"]))
            invoice_previous_subscription_ids = list(map(lambda line: line.id, invoice.subscription_line_ids))
            # invoice_total = sum(map(lambda line: line.price_unit, lines["related_subscriptions"]))
            # invoice_previous_total = sum(map(lambda line: line.price_unit, invoice.subscription_line_ids))
            if invoice_included_subscription_ids == invoice_previous_subscription_ids:
                return False
            invoice2update = {
                "invoice_user_id": self.env.user.id,
                "invoice_origin": "/".join(invoice_origin.keys()),
                "is_co_op": is_co_op or invoice.is_co_op,
                "invoice_line_ids": list(map(lambda line: (2, line.id), invoice.invoice_line_ids))
                + [(0, 0, x) for x in lines["invoice_lines"]],
                "subscription_line_ids": list(map(lambda line: line.id, lines["related_subscriptions"])),
            }
            invoice_type_settings["state"] = "draft"
            invoice2update.update(invoice_type_settings)
            invoice.update(invoice2update)
        else:
            new_invoice = {
                # "ref": order.client_order_ref,
                # "type": "out_invoice",
                "invoice_origin": "/".join(invoice_origin.keys()),
                "invoice_user_id": self.env.user.id,
                "narration": last_order.note,
                "partner_id": partner.id,
                "fiscal_position_id": partner.property_account_position_id.id,
                "partner_shipping_id": last_order.partner_shipping_id.id,
                "currency_id": last_order.pricelist_id.currency_id.id,
                "invoice_payment_ref": last_order.reference,
                "invoice_payment_term_id": last_order.payment_term_id.id,
                "invoice_partner_bank_id": partner.bank_ids[:1].id,
                "is_co_op": is_co_op,
                "team_id": last_order.team_id.id,
                "campaign_id": last_order.campaign_id.id,
                "medium_id": last_order.medium_id.id,
                "source_id": last_order.source_id.id,
                "invoice_payment_state": "not_paid",
                "invoice_date": date.today(),
                "invoice_month_year": self.env["account.move"].invoices_date_signature(kwargs["start_date"]),
                "invoice_line_ids": [(0, 0, x) for x in lines["invoice_lines"]],
                "subscription_line_ids": list(map(lambda line: line.id, lines["related_subscriptions"])),
                # [(0, 0, x) for x in lines["related_subscriptions"]],
            }
            new_invoice.update(invoice_type_settings)
            invoice = self.env["account.move"].create(new_invoice)

        return invoice

    def _grouping_wrapper(
        self, start_date, partner_id=False, subscripion_line=False, grouping_levels=grouping_data.ALL_FLAGS_GROUPING
    ):
        def initial_order_data(line, partner_id):
            price = line.period_price_calc(start_date, partner_id)
            product_variant = ""
            if len(line.product_id.product_template_attribute_value_ids):
                product_variant = line.product_id.product_template_attribute_value_ids[0].name
            rebate, rebate_product = line.rebate_calc(price)
            return {
                "product_name": line.product_id.name,
                "product_variant": product_variant,
                "product_id": line.product_id.id,
                "product_variant": line.product_id.product_template_attribute_value_ids.name or "",
                "name": line.name,
                "price_unit": price,
                "pricelist": line.analytic_account_id.pricelist_id,
                "category_name": line.product_id.categ_id.name,
                "category_id": line.product_id.categ_id.id,
                "description": line._grouping_name_calc(line)
                if grouping_levels & grouping_data.ACCOUNTING_GROUPING_FLAG
                else line.product_id.categ_id.name,  # second level of grouping - budget wrapping
                "contract_product_description": line.product_id.contract_product_description,
                "rebate": rebate,
                "rebate_product": rebate_product,
                "discount": line.discount,
                "tax_ids": list(map(lambda tax: tax.id, line.so_line_id.tax_id)),
                "start_date": line.start_date,
                "end_date": line.end_date,
            }

        def last_order_data(product_individual):
            return {
                "product_name": product_individual["product_name"],
                "product_variant": product_individual["product_variant"],
                "price_unit": product_individual["price_unit"],
                "description": product_individual["description"],
                "contract_product_description": product_individual["contract_product_description"],
                "name": product_individual["name"],
                "rebate": product_individual["rebate"],
                "rebate_product": product_individual["rebate_product"],
                "category_id": product_individual["category_id"],
                "product_id": product_individual["product_id"],
                "pricelist": product_individual["pricelist"],
                "tax_ids": product_individual["tax_ids"],
                "discount": product_individual["discount"],
                "start_date": product_individual["start_date"],
                "end_date": product_individual["end_date"],
                # "prorate_amount": product_individual["prorate_amount"],
                # "product_template_id": product_individual["product_template_id"],
                # "management_fee_calculated": product_individual["management_fee_calculated"],
            }

        def last_order_update(product_source, product_additional):
            product_updated = product_source
            product_updated["price_unit"] += product_additional["price_unit"]
            product_updated["rebate"] += product_additional["rebate"]
            if "start_date" in product_updated or "start_date" in product_additional:
                if not product_updated["start_date"]:
                    product_updated["start_date"] = product_additional["start_date"]
                else:
                    product_updated["start_date"] = (
                        product_additional["start_date"]
                        if product_additional["start_date"]
                        and product_updated["start_date"] > product_additional["start_date"]
                        else product_updated["start_date"]
                    )

            if "end_date" in product_updated:
                if not product_updated["end_date"]:
                    product_updated["end_date"] = product_additional["end_date"]
                else:
                    product_updated["end_date"] = (
                        product_updated["end_date"]
                        if product_additional["end_date"]
                        and product_updated["end_date"] >= product_additional["end_date"]
                        else product_additional["end_date"]
                    )
            # product_updated["prorate_amount"] += product_additional["prorate_amount"]
            return product_updated

        source_lines = subscripion_line or self.recurring_invoice_line_ids
        return self.env["sale.order"].grouping_all_products(
            source_lines, partner_id, initial_order_data, last_order_data, last_order_update, grouping_levels
        )

    def get_subscription_lines(self, partner, order_id, start_date, end_date):
        """
        Collecting lines for invoicing based on the daterange
        Should be start_day and end_day presented
        """
        # collecting filter basing on arguments
        search_args = [
            ("so_line_id.order_id.state", "in", ("sale", "done")),
            "|",
            ("end_date", ">=", start_date),
            ("end_date", "=", False),
            ("start_date", "<=", end_date),
        ]

        if order_id:
            search_args += [("so_line_id.order_id.id", "=", order_id)]

        search_args += [
            "|",
            ("so_line_id.order_id.partner_id", "child_of", partner.id),
            ("analytic_account_id.co_op_partner_ids.partner_id", "in", [partner.id]),
            # co-op change!!!!
            # ("so_line_id.order_id.co_op_sale_order_partner_ids", "in", [partner.id]),
        ]
        return self.env["sale.subscription.line"].with_context(active_test=False).search(search_args)

    def invoicing_add_management_fee_and_rebate_lines(self, grouped_sub_lines, start_date, end_date):
        period_msg = self.format_period_message(start_date, end_date)
        # processing the grouped lines into invoice lines
        rebate_total = {}
        grouped_invoice_lines = []
        for line in grouped_sub_lines:
            if line["price_unit"] == 0:
                continue
            final_price = line["price_unit"]
            if line["management_fee"] > 0:
                final_price -= line["management_fee"]
                grouped_invoice_lines.append(
                    {
                        "name": period_msg,
                        "description": line["description"],
                        "product_id": line["product_id"],
                        "category_id": line["category_id"],
                        "price_unit": final_price,
                        "price_subtotal": final_price,
                        "discount": line["discount"],
                        "tax_ids": line["tax_ids"],
                    }
                )
                management_fee_params = {
                    "description": "Management Fee for " + line["description"],
                    "product_id": False,
                    "category_id": line["category_id"],
                }
                if "management_fee_product" in line and line["management_fee_product"].id:
                    management_fee_params = {
                        "description": line["management_fee_product"].name,
                        "category_id": line["management_fee_product"].categ_id.id,
                        "product_id": line["management_fee_product"].id,
                    }

                grouped_invoice_lines.append(
                    {
                        **{
                            "name": period_msg,
                            "price_unit": line["management_fee"],
                            "price_subtotal": line["management_fee"],
                            "discount": 0,
                            "tax_ids": line["tax_ids"],
                        },
                        **management_fee_params,
                    }
                )
            else:
                grouped_invoice_lines.append(
                    {
                        "name": period_msg,
                        "description": line["description"],
                        "product_id": line["product_id"],
                        "category_id": line["category_id"],
                        "price_unit": line["price_unit"],
                        "price_subtotal": final_price,
                        "discount": line["discount"],
                        "tax_ids": line["tax_ids"],
                    }
                )
            if line["rebate"]:
                rebate_signature = "Rebate Discount"
                if "name" in line["rebate_product"]:
                    rebate_signature = line["rebate_product"].name
                if rebate_signature not in rebate_total:
                    rebate_total[rebate_signature] = {
                        "price": 0.0,
                        "category": None
                        if "categ_id" not in line["rebate_product"]
                        else line["rebate_product"].categ_id.id,
                        "product": None if "id" not in line["rebate_product"] else line["rebate_product"].id,
                        "tax_ids": line["tax_ids"],
                    }

                rebate_total[rebate_signature]["price"] += line["rebate"]

        for reb in rebate_total:
            if rebate_total:
                grouped_invoice_lines.append(
                    {
                        "name": reb,
                        "description": reb,
                        "price_unit": -rebate_total[reb]["price"],
                        "price_subtotal": -rebate_total[reb]["price"],
                        "category_id": rebate_total[reb]["category"],
                        "product_id": rebate_total[reb]["product"],
                        "tax_ids": rebate_total[reb]["tax_ids"],
                    }
                )
        return grouped_invoice_lines

    # grouping levels:
    # 1: budget grouping
    # 2: products
    # 4: description grouping
    # 8: daterange

    def subscription_lines_collection_for_invoicing(self, partner, order_id, start_date, end_date, grouping_levels=7):

        subscription_lines = self.get_subscription_lines(partner, order_id, start_date, end_date)
        invoices_posted = ("posted", "email_sent")
        invoices_could_be_changed = ("draft", "approved_draft")
        if not len(subscription_lines):
            return False

        sub_lines = []
        draft_invoice_subscriptions = {}
        draft_invoices = {}
        response = {}

        # filter out invoiced subscription lines and collect draft invoices for update
        for subscription_line in subscription_lines:
            # find the invoices could be changed
            invoice = self.are_invoices_for_period(partner.id, start_date, invoices_could_be_changed+invoices_posted, subscription_line)
            if invoice and (invoice.state in invoices_could_be_changed):
                draft_invoice_subscriptions[subscription_line.id] = subscription_line
                draft_invoices[invoice.id] = True
                sub_lines.append(subscription_line)
            elif not invoice or (invoice.state not in invoices_posted):
                #in case of subscription was not invoiced ye or invoice was cancelled
                sub_lines.append(subscription_line)

        # if subscriptions are new (nothing was invoiced before) but we still have draft invoice could be updated
        if len(draft_invoices.keys()) == 0:
            invoice = self.are_invoices_for_period(partner.id, start_date, invoices_could_be_changed)
            if invoice and len(invoice) > 0:
                draft_invoices[invoice[0].id] = True
                for line in invoice[0].subscription_line_ids:
                    sub_lines.append(line)

        # more than 2 draft invoices for the month - ask user to manage this
        if len(draft_invoices.keys()) > 1:
            raise UserError(
                "System alredy has more than 1 draft invoice for %s on %s, %s"
                % (partner.name, calendar.month_name[start_date.month], start_date.year)
            )

        if len(draft_invoices.keys()) == 1:
            response.update({"draft_invoice": list(draft_invoices.keys())[0]})
        # adding rebate to subscriptions before grouping

        # invoice lines grouping - products and description only
        grouped_sub_lines = self._grouping_wrapper(start_date, partner.id, sub_lines, grouping_levels)

        grouped_invoice_lines = self.invoicing_add_management_fee_and_rebate_lines(
            grouped_sub_lines, start_date, end_date
        )

        response.update({"invoice_lines": grouped_invoice_lines, "related_subscriptions": sub_lines})
        return response


class SaleSubscriptionLine(models.Model):
    """
    Inherited to setup fields for invoice like.
        Start & End Date : Shows invoice cycle
        Last Invoiced: To store last invoice generated date
    """

    _inherit = "sale.subscription.line"

    # as invoicing part was rewritten these fields could be removed:
    # last_invoiced invoice_start_date invoice_end_date cancel_invoice_start_date cancel_invoice_end_date
    last_invoiced = fields.Date(string="Last Invoiced")
    invoice_start_date = fields.Date("Start Date")
    invoice_end_date = fields.Date("End Date")
    cancel_invoice_start_date = fields.Date("Cancel Start Date")
    cancel_invoice_end_date = fields.Date("Cancel End Date")
    account_id = fields.Many2one("account.move", string="Invoice")
    prorate_amount = fields.Float(related="so_line_id.prorate_amount", string="Prorate Start Amount", readonly=False)
    prorate_end_amount = fields.Float(string="Prorate End Amount")

    def _creation_next_budgets(self):
        print("CRON CRON CRON")

    def write(self, vals):
        res = super(SaleSubscriptionLine, self).write(vals)

    def start_in_next(self):
        """
        To map with invoice and service start date of to manage Advance + N
        Amount will be calculated bases on Current month and if any service start with advance month it will consider in invoice
        For example:    Advance + 2  Current Month August then invoice will August + September + October\n
                        Start      - End        Amount = Total \n
                        08/01/2020 - 10/31/2020 1000   = 3000 \n
                        09/01/2020 - 12/31/2021 500    = 1000 \n
                        10/01/2020 - 02/28/2021 300    = 0300 \n
                                                         4300 \n
        :return: Total number of months.
        """
        ad_lines = self.env["sale.subscription.line"]
        today = date.today().replace(day=1)
        # policy_month = self.so_line_id.order_id.clx_invoice_policy_id.num_of_month
        end_date = today + relativedelta(months=1, days=-1)
        return 0 if self.invoice_start_date > end_date else 1

    # calculation rebates. Taking from the management company settings
    def rebate_calc(self, price):
        management_company = self.analytic_account_id.partner_id.management_company_type_id
        if not management_company:
            return 0.0, None

        total_discount = (price * management_company.discount_on_order_line) / 100
        discount_product = None
        if management_company.discount_product:
            discount_product = management_company.discount_product
        if (
            management_company.is_flat_discount
            and management_company.clx_category_id
            and "categ_id" in self.analytic_account_id.product_id
            and self.analytic_account_id.product_id.categ_id.id == management_company.clx_category_id.id
        ):
            total_discount = management_company.flat_discount
            if management_company.discount_product:
                discount_product = management_company.flat_discount_product
        elif (
            management_company.is_percent_discount
            and management_company.percent_discount_category_id
            and "categ_id" in self.analytic_account_id.product_id
            and self.analytic_account_id.product_id.categ_id.id == management_company.percent_discount_category_id.id
        ):
            total_discount = (price * management_company.percent_discount) / 100
            if management_company.percent_discount_product:
                discount_product = management_company.percent_discount_product

        return total_discount, discount_product

    # calculation price for period. Taking into account proration
    def period_price_calc(self, start_date, partner_id, dont_prorate=False):
        end_date_for_period = start_date + relativedelta(months=1) + relativedelta(days=-1)
        if end_date_for_period < self["start_date"] or (self["end_date"] and start_date > self["end_date"]):
            return 0.0

        price_calculated = self["price_unit"]
        if (
            start_date.month == self["start_date"].month
            and start_date.year == self["start_date"].year
            and self["prorate_amount"]
        ):
            price_calculated = self["prorate_amount"]
        if (
            self["end_date"]
            and start_date.month == self["end_date"].month
            and start_date.year == self["end_date"].year
            and self["prorate_end_amount"]
        ):
            price_calculated = self["prorate_end_amount"]
        co_op_coef = 1
        # co-op change!!!!
        co_op_list = self.analytic_account_id.co_op_partner_ids
        if partner_id and len(co_op_list) and not dont_prorate:
            coop_line_filter = filter(lambda line: line.partner_id.id == partner_id, co_op_list)
            if len(list(coop_line_filter)) == 0:
                co_op_coef = 0
            else:
                co_op_coef = next(filter(lambda line: line.partner_id.id == partner_id, co_op_list)).ratio / 100
        # if co_op_coef > 1:
        #     co_op_coef /= 100
        price_calculated = co_op_coef * price_calculated
        return price_calculated

    # could be removed after refactoring Vlad
    def get_date_month(self, end, start):
        """
        To get interval between dates in month to compute invoices
        Formula    : (end.year - start.year) * 12 + end.month - start.month \n
        For example:    Start      - End        = Difference \n
                        08/10/2020 - 10/31/2020 = 2 \n
                        09/15/2020 - 12/31/2021 = 4 \n
                        10/10/2020 - 02/28/2021 = 5 \n
        :param end: Last date of interval
        :param start: Start date of interval
        :return: Total number of months
        """

        return len(OrderedDict(((start + timedelta(_)).strftime("%B-%Y"), 0) for _ in range((end - start).days)))
        # return (end.year - start.year) * 12 + end.month - start.month

    # old SB's code
    def _format_period_msg(self, date_start, date_end, line, inv_start=False, inv_end=False):
        """
        To calculate invoice period/adjustment date
        :return: Formatted String
        """
        lang = line.order_id.partner_invoice_id.lang
        format_date = self.env["ir.qweb.field.date"].with_context(lang=lang).value_to_html
        if (
            line.order_id.clx_invoice_policy_id.policy_type == "advance"
            and self.line_type == "upsell"
            and not self.last_invoiced
        ):
            return "%s: %s - %s" % (
                _("Invoice Adjustment"),
                format_date(fields.Date.to_string(inv_start), {}),
                format_date(fields.Date.to_string(inv_end), {}),
            )
        elif line.order_id.clx_invoice_policy_id.policy_type == "arrears":
            return "%s: %s - %s" % (
                _("Invoicing period"),
                format_date(fields.Date.to_string(date_start), {}),
                format_date(fields.Date.to_string(date_end), {}),
            )
        elif inv_start and inv_end:
            return "%s: %s - %s" % (
                _("Invoicing period"),
                format_date(fields.Date.to_string(inv_start), {}),
                format_date(fields.Date.to_string(inv_end), {}),
            )
        else:
            return "%s: %s - %s" % (
                _("Invoicing period"),
                format_date(fields.Date.to_string(date_start), {}),
                format_date(fields.Date.to_string(date_end), {}),
            )

    def _grouping_name_calc(self, line):
        description = line.product_id.categ_id.name
        partner_id = line.so_line_id.order_id.partner_id
        product_id = line.product_id
        if partner_id.invoice_selection == "sol":
            description = self.env["sale.order.line"]._grouping_by_product_logic(product_id, partner_id, line.name)

        return description

    def _prepare_invoice_line(self):
        """
        Prepare the dict of values to create the new invoice line.
        :return: Dictionary of formatted values
        """
        self.ensure_one()
        line = self.so_line_id
        today = date.today()
        date_start = line.start_date
        date_end = date_start + relativedelta(months=1, days=-1)
        period_msg = self._format_period_msg(date_start, date_end, line, self.invoice_start_date, self.invoice_end_date)
        policy_month = self.so_line_id.order_id.clx_invoice_policy_id.num_of_month + 1
        res = {
            "display_type": line.display_type,
            "sequence": line.sequence,
            "name": period_msg,
            "subscription_id": self.analytic_account_id.id,
            # "subscription_ids": [(6, 0, self.analytic_account_id.ids)],
            "subscription_start_date": self.start_date,
            "subscription_end_date": date_end,
            "product_id": self.product_id.id,
            "category_id": self.product_id.categ_id.id,
            "product_uom_id": line.product_uom.id,
            "quantity": 1,
            "discount": 0.0,
            "price_unit": self.price_unit,
            "tax_ids": [(6, 0, line.tax_id.ids)],
            "analytic_account_id": line.order_id.analytic_account_id.id,
            "analytic_tag_ids": [(6, 0, line.analytic_tag_ids.ids)],
            "line_type": self.line_type,
            "sale_line_ids": line.ids,
        }
        # update prices if lines has proration
        if self.invoice_start_date and self.start_date.month == self.invoice_start_date.month:
            new_price = self.prorate_amount if self.prorate_amount > 0 else self.price_unit
            res.update(
                {
                    "price_unit": new_price,
                }
            )
        if self.invoice_end_date and self.end_date and self.end_date.month == self.invoice_end_date.month:
            new_price = self.prorate_end_amount if self.prorate_end_amount > 0 else self.price_unit
            res.update(
                {
                    "price_unit": new_price,
                }
            )
        if line.display_type:
            res["account_id"] = False
        if self._context.get("advance", False):
            product_qty = 1
            end_date = self.invoice_end_date
            if self.so_line_id.order_id.partner_id.invoice_creation_type == "separate":
                policy_month = 1
            period_msg = self._format_period_msg(
                date_start, date_end, line, self.invoice_start_date, self.invoice_end_date
            )
            vals = {
                "last_invoiced": today,
                "invoice_start_date": False,
                "invoice_end_date": False,
            }
            expire_date = False
            if self.invoice_end_date:
                expire_date = (self.invoice_end_date + relativedelta(months=policy_month + 1)).replace(
                    day=1
                ) + relativedelta(days=-1)
            vals.update(
                {
                    "invoice_start_date": (self.invoice_end_date + relativedelta(months=1)).replace(day=1)
                    if self.invoice_end_date
                    else False,
                    "invoice_end_date": expire_date,
                }
            )
            # if not self.end_date:
            if line.product_id.subscription_template_id.recurring_rule_type == "yearly":
                yearly_start_date = (
                    (self.invoice_end_date + relativedelta(months=1)).replace(day=1) if self.invoice_end_date else False
                )
                yearly_end_date = (yearly_start_date + relativedelta(months=12)).replace(day=1) + relativedelta(days=-1)
                vals.update({"invoice_start_date": yearly_start_date, "invoice_end_date": yearly_end_date})
                lang = line.order_id.partner_invoice_id.lang
                format_date = self.env["ir.qweb.field.date"].with_context(lang=lang).value_to_html
                period_msg = ("Invoicing period: %s - %s") % (
                    format_date(fields.Date.to_string(self.invoice_start_date), {}),
                    format_date(fields.Date.to_string(self.invoice_end_date), {}),
                )
                res.update(
                    {
                        "name": period_msg,
                        "price_unit": self.price_unit * 12,
                        "description": self._grouping_name_calc(line),
                    }
                )
                self.with_context(skip=True).write(vals)
                return res
            if not self._context.get("generate_invoice_date_range", False):
                self.with_context(skip=True).write(vals)
            if self.end_date:
                if (
                    self.invoice_start_date
                    and self.invoice_end_date
                    and self.invoice_start_date <= self.end_date <= self.invoice_end_date
                ):
                    self.with_context(skip=True).write({"invoice_end_date": self.end_date})
                elif (
                    self.invoice_start_date
                    and self.invoice_start_date > self.end_date
                    and not self._context.get("generate_invoice_date_range", False)
                ):
                    self.with_context(skip=True).write({"invoice_end_date": False, "invoice_start_date": False})
            res.update(
                {
                    "name": period_msg,
                    "subscription_end_date": self.end_date
                    if self.end_date and self.end_date > date_end
                    else expire_date,
                }
            )
            if self._context.get("generate_invoice_date_range", False):
                start_date = self.start_date
                end_date = self.end_date
                lang = line.order_id.partner_invoice_id.lang
                format_date = self.env["ir.qweb.field.date"].with_context(lang=lang).value_to_html

                count = len(
                    OrderedDict(
                        ((self._context.get("start_date") + timedelta(_)).strftime("%B-%Y"), 0)
                        for _ in range((self._context.get("end_date") - self._context.get("start_date")).days)
                    )
                )
                if self.product_id.subscription_template_id.recurring_rule_type == "monthly":
                    period_msg = ("Invoicing period: %s - %s") % (
                        format_date(fields.Date.to_string(self._context.get("start_date")), {}),
                        format_date(fields.Date.to_string(self._context.get("end_date")), {}),
                    )
                    if self.invoice_end_date:
                        expire_date = (self.invoice_end_date + relativedelta(months=2)).replace(day=1) + relativedelta(
                            days=-1
                        )
                        vals.update(
                            {
                                "invoice_start_date": (self.invoice_end_date + relativedelta(months=1)).replace(day=1)
                                if self.invoice_end_date
                                else False,
                                "invoice_end_date": expire_date,
                            }
                        )
                        self.write(vals)
                res.update(
                    {
                        "name": period_msg,
                    }
                )

                if self.start_date and self._context.get("start_date").month == start_date.month:
                    new_price = self.prorate_amount if self.prorate_amount > 0 else self.price_unit
                    res.update(
                        {
                            "price_unit": new_price,
                        }
                    )
                if self.end_date and self._context.get("end_date").month == end_date.month:
                    new_price = self.prorate_end_amount if self.prorate_end_amount > 0 else self.price_unit
                    res.update(
                        {
                            "price_unit": new_price,
                        }
                    )
        res.update({"description": self._grouping_name_calc(line)})
        if self._context.get("co_op", False):
            price_unit = (res["price_unit"] * self._context.get("percantage")) / 100
            res.update({"price_unit": price_unit})
        return res
