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

from odoo.tools.misc import Reverse
from . import grouping_data

INVOICE_LINE_MESSAGE_TEMPLATE = "Invoicing period: %s - %s"


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    clx_invoice_policy_id = fields.Many2one("clx.invoice.policy", string="Invoice Policy")
    management_fee_grouping = fields.Boolean(related="partner_id.management_fee_grouping", readonly=True)

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

    # Calculate the management fee and wholesale for group of subscriptions.
    # Supposing the list contains the lines for certain period
    # All inputs should be collecteded to represent a lines need to have Mgmnt. Fee as one piece
    def update_subscriptions_with_management_fee(self, partner_id, subscription_list, category_show_params=False):
        zero_management = {
            "management_fee": 0,
            "wholesale_price": 0,
            "management_fee_product": False,
        }

        # if partner_id.management_fee_grouping:
        # populate the source lines with management fee and wholesale data
        grouped_products = {}
        for subscription in subscription_list:
            # remove the zero spending budgets from the management fee spreading list
            if subscription["price_unit"] == 0:
                subscription.update(zero_management)
                continue
            if subscription["product_id"] not in grouped_products:
                grouped_products[subscription["product_id"]] = []
            grouped_products[subscription["product_id"]].append(subscription)

        for subscriptions_set in grouped_products:
            subscriptions_by_product = grouped_products[subscriptions_set]
            retail = 0.0
            price_full_month = 0.0
            if category_show_params and subscriptions_by_product[0]["category_id"] in category_show_params:
                category_show = category_show_params[subscriptions_by_product[0]["category_id"]]
            else:
                category_show = False
            pricelist = subscriptions_by_product[0]["pricelist"]

            for subscription in subscriptions_by_product:
                retail += subscription["price_unit"] / subscription["coop_coef"]
                price_full_month += subscription["price_full"] / subscription["coop_coef"]

            fees_obj = self.subscription_wholesale_period(
                retail,
                pricelist,
                price_full_month,
                category_show,
            )

            cost_of_prorated_point = 0 if price_full_month == 0 else fees_obj["management_fee"] / price_full_month
            cost_of_prorated_point_wholesale = (
                0 if price_full_month == 0 else fees_obj["wholesale_price"] / price_full_month
            )

            for subscription in subscriptions_by_product:
                if cost_of_prorated_point == 0 and cost_of_prorated_point_wholesale == 0:
                    subscription.update(zero_management)
                    continue

                management_fee = subscription["price_full"] * cost_of_prorated_point

                wholesale_price = (
                    subscription["price_unit"] - round(management_fee, 2)
                    if management_fee != 0
                    else subscription["price_full"] * cost_of_prorated_point_wholesale
                )

                subscription.update(
                    {
                        "management_fee": round(management_fee, 2),
                        "wholesale_price": wholesale_price,
                        "management_fee_product": fees_obj["management_fee_product"],
                    }
                )

    # splitting the retail price to wholesale and management fee following the pricelist rules.
    # show_flags - is management fee and wholesale need to be shown
    # full_month_price - price for not-prorated month
    # requested to have the 50% manaement fee calculation for any prorated month what means spending for whole month != the current month retail
    def subscription_wholesale_period(
        self,
        retail,
        price_list,
        full_month_price=0.0,
        show_flags={
            "show_mgmnt_fee": True,
            "show_wholesale": True,
        },
    ):
        price_process = full_month_price
        # coef for prorated month
        if full_month_price == retail or full_month_price == 0.0:
            coef = 1
        else:
            coef = 0.5

        if not price_list or not price_list.active:
            return {
                "management_fee": False,
                "wholesale_price": False,
                "management_fee_product": False,
            }

        if retail == 0:
            return {"management_fee": 0, "wholesale_price": 0, "management_fee_product": False}

        management_fee = 0.0 if show_flags and show_flags["show_mgmnt_fee"] else False
        wholesale = 0.0 if show_flags and show_flags["show_wholesale"] else False
        management_fee_product = (
            None if "management_fee_product" not in price_list else price_list.management_fee_product
        )
        retail_absolute = abs(retail)
        full_retail_absolute = abs(price_process)
        if price_list.is_custom and management_fee == 0.0:
            if full_retail_absolute <= price_list.min_retail_amount:
                management_fee = price_list.fixed_mgmt_price
            else:
                management_fee = round((price_list.percent_mgmt_price * full_retail_absolute) / 100, 2)
        else:
            # if management fee fixed
            if (
                price_list.is_fixed
                and price_list.fixed_mgmt_price
                and show_flags
                and show_flags["show_mgmnt_fee"]
                and retail_absolute > price_list.fixed_mgmt_price
            ):
                management_fee = price_list.fixed_mgmt_price

            # if management fee percentage
            if (
                price_list.is_percentage
                and price_list.percent_mgmt_price
                and show_flags
                and show_flags["show_mgmnt_fee"]
            ):
                management_fee = round((price_list.percent_mgmt_price * full_retail_absolute) / 100, 2)

            # if wholesale fee percentage
            if (
                price_list.is_wholesale_percentage
                and price_list.percent_wholesale_price
                and show_flags
                and show_flags["show_wholesale"]
            ):
                wholesale = round((price_list.percent_wholesale_price * retail_absolute) / 100, 2)

        # but never less than minimum price
        if management_fee < price_list.fixed_mgmt_price and price_list.is_fixed:
            management_fee = price_list.fixed_mgmt_price

        management_fee = management_fee * coef

        if wholesale == 0.0 and management_fee != 0.0:
            wholesale = retail_absolute - management_fee

        # invert the management fee when retail is negative
        if retail != retail_absolute:
            management_fee = -management_fee
            wholesale = -wholesale

        return {
            "management_fee": management_fee,
            "wholesale_price": wholesale,
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

        invoices_generate_since_str = self.env["ir.config_parameter"].sudo().get_param("invoices_generate_since", False)
        invoices_generate_since = (
            False
            if not fields.Date.to_date(invoices_generate_since_str)
            else fields.Date.to_date(invoices_generate_since_str)
        )
        if invoices_generate_since and kwargs["start_date"] < invoices_generate_since:
            return False

        order_id = kwargs["order_id"] if "order_id" in kwargs else False

        partner_id = kwargs["partner_id"]

        partner = self.env["res.partner"].browse(partner_id)

        # get all subscription lines
        lines = self.subscription_lines_collection_for_invoicing(
            partner, order_id, kwargs["start_date"], kwargs["end_date"], grouping_data.DESCRIPTION_GROUPING_FLAG
        )

        # do not create invoices if no lines to invoice or all have 0
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
        # checking if current invoice process with child company
        coop_partners_set = list(
            map(
                lambda l: l.analytic_account_id.co_op_partner_ids.mapped("partner_id.id"),
                lines["related_subscriptions"],
            )
        )
        coop_partners = []
        for partner_set in coop_partners_set:
            coop_partners += partner_set

        # search for coops partners(childs_only) to invoice them:
        if is_co_op and not partner.id in coop_partners:
            kwargs_coop = kwargs.copy()

            for coop_partner in set(coop_partners):
                kwargs_coop["partner_id"] = coop_partner
                self.invoicing_one_period(**kwargs_coop)

        last_order = sorted(
            lines["related_subscriptions"], key=lambda kv: kv.so_line_id.order_id.create_date, reverse=True
        )[0].so_line_id.order_id

        # generating the new invoice
        invoice_origin = {}
        for line in lines["related_subscriptions"]:
            invoice_origin[line.so_line_id.order_id.name] = True
        total_invoice_value = sum(map(lambda line: line.price_unit, lines["related_subscriptions"]))

        posted_invoice = False if "posted_invoice" not in lines else lines["posted_invoice"]
        # if total negative - create the credit note. Prepearing the variables
        if total_invoice_value < 0:
            # reverting valaues
            for line in lines["invoice_lines"]:
                line["price_unit"] = -line["price_unit"]
                line["price_subtotal"] = -line["price_subtotal"]

            invoice_type_settings = {
                "ref": "Credit note",
                "type": "out_refund",
            }
        else:
            invoice_type_settings = {
                "ref": "Invoice",
                "type": "out_invoice",
            }

        if posted_invoice and "id" in posted_invoice:
            invoice_type_settings.update(
                {
                    "reversed_entry_id": posted_invoice.id,
                }
            )

        if "draft_invoice" in lines:
            # updating the draft invoice
            invoice = lines["draft_invoice"]
            invoice_included_subscription_ids = list(map(lambda line: line.id, lines["related_subscriptions"]))
            invoice_previous_subscription_ids = list(map(lambda line: line.id, invoice.subscription_line_ids))
            # invoice_total = sum(map(lambda line: line.price_unit, lines["related_subscriptions"]))
            # invoice_previous_total = sum(map(lambda line: line.price_unit, invoice.subscription_line_ids))
            invoice2update = {
                "state": "draft",
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

    # grouping all subscriptions following the grouping rules for reporting
    # start_date, partner_id=False, subscripion_line=False, grouping_levels=grouping_data.ALL_FLAGS_GROUPING
    def _grouping_wrapper(self, **kwargs):
        # inputs process
        if not "start_date" in kwargs:
            return []
        start_date = kwargs["start_date"]
        partner_id = kwargs.get("partner_id", False)
        subscripion_line = kwargs.get("subscripion_line", False)
        grouping_levels = kwargs.get("grouping_levels", grouping_data.ALL_FLAGS_GROUPING)
        contract_mode = kwargs.get("contract_mode", False)
        def initial_order_data(line, partner_id):
            price, price_full, coop_coef = line.period_price_calc(start_date, partner_id, contract_mode)
            product_variant = ""
            if len(line.product_id.product_template_attribute_value_ids):
                product_variant = line.product_id.product_template_attribute_value_ids[0].name
            rebate, rebate_product = line.rebate_calc(price)
            pricelist2process = line.analytic_account_id.pricelist_determination(
                line.product_id, line.analytic_account_id.pricelist_id
            )

            return {
                "id": line.id,
                "product_name": line.product_id.name,
                "product_variant": product_variant,
                "partner_owner": line.analytic_account_id.partner_id,
                "product_id": line.product_id.id,
                "coop_coef": coop_coef,
                "product_variant": line.product_id.product_template_attribute_value_ids.name or "",
                "name": line.name,
                # when calling the function without the authorization (from API) we don't have the current company
                # so need to define it explicetly for fields depends on company .
                # Now the main company is only one so we can use it's ID - 1
                "account_id": line.analytic_account_id.with_context(
                    {"force_company": 1}
                ).account_depreciation_expense_id.id
                or False,
                "price_unit": price,
                "price_full": price_full,
                "pricelist": pricelist2process,
                "category_name": line.product_id.categ_id.name,
                "category_id": line.product_id.categ_id.id,
                "description": line._grouping_name_calc(line)
                if grouping_levels & grouping_data.ACCOUNTING_GROUPING_FLAG
                else line.name,  # second level of grouping - budget wrapping
                "contract_product_description": line.product_id.contract_product_description,
                "rebate": rebate,
                "rebate_product": rebate_product,
                "discount": line.discount,
                "tax_ids": list(map(lambda tax: tax.id, line.so_line_id.tax_id)),
                "start_date": line.start_date,
                "end_date": line.end_date,
            }

        # just filtering the fields necessary for last step - invoice creation
        def last_order_data(product_individual):
            return {
                "product_name": product_individual["product_name"],
                "product_variant": product_individual["product_variant"],
                "price_unit": product_individual["price_unit"],
                "description": product_individual["description"],
                "contract_product_description": product_individual["contract_product_description"],
                "account_id": product_individual["account_id"],
                "name": product_individual["name"],
                "rebate": product_individual["rebate"],
                "rebate_product": product_individual["rebate_product"],
                "category_id": product_individual["category_id"],
                "product_id": product_individual["product_id"],
                "partner_owner": product_individual["partner_owner"],
                "pricelist": product_individual["pricelist"],
                "price_full": product_individual["price_full"],
                "wholesale_price": product_individual["wholesale_price"],
                "tax_ids": product_individual["tax_ids"],
                "discount": product_individual["discount"],
                "start_date": product_individual["start_date"],
                "end_date": product_individual["end_date"],
                "management_fee": product_individual["management_fee"],
                "management_fee_product": product_individual["management_fee_product"],
                # "prorate_amount": product_individual["prorate_amount"],
                # "product_template_id": product_individual["product_template_id"],
                # "management_fee_calculated": product_individual["management_fee_calculated"],
            }

        def last_order_update(product_source, product_additional):
            product_updated = product_source
            product_updated["price_unit"] += product_additional["price_unit"]
            product_updated["price_full"] += product_additional["price_full"]
            product_updated["management_fee"] += product_additional["management_fee"]
            product_updated["management_fee_product"] = (
                product_updated["management_fee_product"] or product_additional["management_fee_product"]
            )
            product_updated["wholesale_price"] += product_additional["wholesale_price"]
            product_updated["rebate"] += product_additional["rebate"]
            product_updated["account_id"] = product_additional["account_id"]
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
            source_lines,
            partner_id,
            initial_order_data,
            last_order_data,
            last_order_update,
            start_date,
            grouping_levels,
        )

    """ Collecting the subscription lines need to be combined for management fee calculation
    Input: 
        mandatory: partner, start_date, 
        optional: order, product, end_date, 
    """

    def get_subscription_lines(self, **kwargs):

        if "partner" not in kwargs or "start_date" not in kwargs:
            return []

        start_date = kwargs["start_date"]
        partner = kwargs["partner"]

        # if end_date not set - set as a last day of the start_date month
        if "end_date" not in kwargs:
            end_date = start_date + relativedelta(months=1, days=-1)
        else:
            end_date = kwargs["end_date"]

        # collecting filter basing on arguments
        search_args = [
            ("so_line_id.order_id.state", "in", ("sale", "done")),
            "|",
            ("end_date", ">=", start_date),
            ("end_date", "=", False),
            ("start_date", "<=", end_date),
        ]

        if "order" in kwargs and kwargs["order"]:
            search_args += [("so_line_id.order_id.id", "=", kwargs["order"].id)]

        if "product" in kwargs:
            search_args += [("so_line_id.product_id.id", "=", kwargs["product"].id)]

        if "exceptions" in kwargs:
            search_args += [("id", "not in", kwargs["exceptions"])]

        if "root_only" in kwargs and kwargs["root_only"]:
            search_args += [
                ("so_line_id.order_id.partner_id", "child_of", partner.id),
            ]
        else:
            search_args += [
                "|",
                ("so_line_id.order_id.partner_id", "child_of", partner.id),
                ("analytic_account_id.co_op_partner_ids.partner_id", "in", [partner.id]),
            ]

        return self.env["sale.subscription.line"].with_context(active_test=False).search(search_args)

    # adding the management fee and rebate lines to the invoice
    def invoicing_add_management_fee_and_rebate_lines(self, grouped_sub_lines, start_date, end_date):
        period_msg = self.format_period_message(start_date, end_date)
        # processing the grouped lines into invoice lines
        rebate_total = {}
        grouped_invoice_lines = []
        management_lines_added = {}
        for line in grouped_sub_lines:
            if line["price_unit"] == 0:
                continue
            final_price = line["price_unit"]
            if abs(line["management_fee"]) > 0:
                final_price -= line["management_fee"]
                grouped_invoice_lines.append(
                    {
                        "name": period_msg,
                        "account_id": line["account_id"],
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
                if "management_fee_product" in line and line["management_fee_product"]:
                    management_fee_params = {
                        "description": line["management_fee_product"].name,
                        "category_id": line["management_fee_product"].categ_id.id,
                        "product_id": line["management_fee_product"].id,
                        "account_id": line["account_id"],
                    }
                management_fee_stamp = line["management_fee_product"].name
                if management_fee_stamp in management_lines_added:
                    management_lines_added[management_fee_stamp]["price_unit"] += line["management_fee"]
                    management_lines_added[management_fee_stamp]["price_subtotal"] += line["management_fee"]
                    management_lines_added[management_fee_stamp]["position"] = len(grouped_invoice_lines)
                else:
                    management_lines_added[management_fee_stamp] = {
                        **{
                            "name": period_msg,
                            "price_unit": line["management_fee"],
                            "price_subtotal": line["management_fee"],
                            "discount": 0,
                            "tax_ids": line["tax_ids"],
                            "position": len(grouped_invoice_lines),
                        },
                        **management_fee_params,
                    }
            else:
                grouped_invoice_lines.append(
                    {
                        "name": period_msg,
                        "account_id": line["account_id"],
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
                if line["rebate_product"] and "name" in line["rebate_product"]:
                    rebate_signature = line["rebate_product"].name
                if rebate_signature not in rebate_total:
                    rebate_total[rebate_signature] = {
                        "price": 0.0,
                        "category": None
                        if not line["rebate_product"] or "categ_id" not in line["rebate_product"]
                        else line["rebate_product"].categ_id.id,
                        "product": None if "id" not in line["rebate_product"] else line["rebate_product"].id,
                        "tax_ids": None,  # line["tax_ids"],
                        "account_id": line["account_id"],
                    }

                rebate_total[rebate_signature]["price"] += line["rebate"]

        management_lines = list(management_lines_added.values())
        for i in range(len(management_lines), 0, -1):
            object_to_insert = management_lines[i - 1]
            position = object_to_insert["position"]
            del object_to_insert["position"]
            grouped_invoice_lines.insert(position, object_to_insert)

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
                        "account_id": rebate_total[reb]["account_id"],
                    }
                )
        return grouped_invoice_lines

    # grouping levels:
    # 1: budget grouping
    # 2: products
    # 4: description grouping
    # 8: daterange

    def subscription_lines_collection_for_invoicing(self, partner, order_id, start_date, end_date, grouping_levels=7):
        draft_invoce_states = ["draft", "approved_draft"]
        posted_invoce_states = ["posted", "email_sent"]
        subscription_lines = self.get_subscription_lines(
            partner=partner, order_id=order_id, start_date=start_date, end_date=end_date
        )
        invoices_could_be_changed = ("draft", "approved_draft")
        if not len(subscription_lines):
            return False

        sub_lines = []
        draft_invoice_subscriptions = {}
        draft_invoices = {}
        response = {}

        # Generating the data for "global" invoice. Imagining like we don't have any invoices (draft or posted) now.
        # invoice lines grouping - products and description only
        global_grouped_sub_lines = self._grouping_wrapper(
            start_date=start_date,
            partner_id=partner,
            subscripion_line=subscription_lines,
            grouping_levels=grouping_levels,
        )

        global_grouped_invoice_lines = self.invoicing_add_management_fee_and_rebate_lines(
            global_grouped_sub_lines.values(), start_date, end_date
        )

        # get list of all invoices for the period
        invoice_object = self.env["account.move"]
        period_msg = invoice_object.invoices_date_signature(start_date)
        all_filters = [
            ("invoice_month_year", "=", period_msg),
            ("partner_id.id", "=", partner.id),
            ("state", "in", draft_invoce_states + posted_invoce_states),
        ]

        all_existing_invoices = invoice_object.search(all_filters)

        # filtering invoices for current period to two categoies: completed (posted/paid) and draft(draft/approved_draft)

        all_draft_invoices = list(filter(lambda i: i.state in draft_invoce_states, all_existing_invoices))
        all_complete_invoices = list(filter(lambda i: i.state in posted_invoce_states, all_existing_invoices))

        # more than 2 draft invoices for the month - ask user to manage this
        if len(all_draft_invoices) > 1:
            raise UserError(
                "System alredy has more than 1 draft invoice for %s on %s, %s"
                % (partner.name, calendar.month_name[start_date.month], start_date.year)
            )
        if len(all_draft_invoices) == 1:
            response.update({"draft_invoice": all_draft_invoices[0]})

        if len(all_complete_invoices) > 0:
            response.update(
                {"posted_invoice": sorted(all_complete_invoices, key=lambda l: l.create_date, reverse=True)[0]}
            )

        # combine all processed invoices into one
        all_paid_spends = {}
        all_subscription_lines_processed = []
        for invoice in all_complete_invoices:
            all_subscription_lines_processed += invoice.subscription_line_ids.mapped("id")
            for product in invoice.invoice_line_ids:
                product_signature = str(product.product_id.id) + product.description
                if product_signature not in all_paid_spends:
                    all_paid_spends[product_signature] = {
                        "price_unit": product.price_unit,
                        "price_subtotal": product.price_subtotal,
                        "name": product.name,
                        "description": product.description,
                        "product_id": product.product_id.id,
                        "category_id": product.category_id,
                        "tax_ids": product.tax_ids.ids,
                        "account_id": product.account_id,
                    }
                else:
                    coef = 1
                    if invoice.type == "out_refund":
                        coef = -1
                    all_paid_spends[product_signature]["price_unit"] += product.price_unit * coef
                    all_paid_spends[product_signature]["price_subtotal"] += product.price_subtotal * coef

        all_new_spends = []
        grouped_invoice_lines = []
        for line in global_grouped_invoice_lines:
            product_signature = str(line["product_id"]) + line["description"]
            all_new_spends.append(product_signature)
            if product_signature in all_paid_spends:
                line["price_subtotal"] -= all_paid_spends[product_signature]["price_subtotal"]
                line["price_unit"] -= all_paid_spends[product_signature]["price_unit"]
            grouped_invoice_lines.append(line)

        # check for the edge case: the complited invoices has the product we don't have in current(it means the product need to be refunded in full)
        for line in [value for value in all_paid_spends.keys() if value not in all_new_spends]:
            refund_line = all_paid_spends[line]
            refund_line["price_unit"] = -refund_line["price_unit"]
            refund_line["price_subtotal"] = -refund_line["price_subtotal"]
            grouped_invoice_lines.append(all_paid_spends[line])

        # only new lines should go to the invoice
        sub_lines = list(filter(lambda i: i.id not in all_subscription_lines_processed, subscription_lines))

        # filter out the zero spend values
        grouped_invoice_lines = list(filter(lambda l: l["price_unit"], grouped_invoice_lines))

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
    management_fee_grouping = fields.Boolean(
        related="analytic_account_id.partner_id.management_fee_grouping",
        readonly=True,
        string="Need Management Fee be grouped?",
    )

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

    # calculation price for period. Taking into account proration and co-op percentage
    def period_price_calc(self, start_date, partner_id, dont_prorate_coop=False, object=None):
        if not object:
            obj_to_process = self
            co_op_list = self.analytic_account_id.co_op_partner_ids
        else:
            obj_to_process = object
            co_op_list = obj_to_process.co_op_sale_order_line_partner_ids

        end_date_for_period = start_date + relativedelta(months=1) + relativedelta(days=-1)
        price_full = obj_to_process["price_unit"]
        if end_date_for_period < obj_to_process["start_date"] or (
            obj_to_process["end_date"] and start_date > obj_to_process["end_date"]
        ):
            return 0.0, price_full, 1

        price_calculated = obj_to_process["price_unit"]

        if (
            start_date.month == obj_to_process["start_date"].month
            and start_date.year == obj_to_process["start_date"].year
            and obj_to_process["prorate_amount"]
        ):
            price_calculated = obj_to_process["prorate_amount"]

        if (
            obj_to_process["end_date"]
            and start_date.month == obj_to_process["end_date"].month
            and start_date.year == obj_to_process["end_date"].year
            and "prorate_end_amount" in obj_to_process
            and not obj_to_process["prorate_end_amount"] == 0
        ):
            price_calculated = obj_to_process["prorate_end_amount"]

        co_op_coef = 1
        # co-op change!!!!
        if partner_id and len(co_op_list) and not dont_prorate_coop:
            coop_line_filter = list(filter(lambda line: line.partner_id.id == partner_id.id, co_op_list))
            if len(coop_line_filter) == 0:
                co_op_coef = 0
            else:
                co_op_coef = coop_line_filter[0].ratio / 100

        price_calculated = co_op_coef * price_calculated
        price_full = co_op_coef * price_full

        return price_calculated, price_full, co_op_coef

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
