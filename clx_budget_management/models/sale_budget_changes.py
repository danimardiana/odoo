# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

import datetime
from dateutil.relativedelta import relativedelta
from odoo import fields, models


class SaleBudgetChanges(models.Model):
    _name = "sale.budget.changes"
    _description = "Sale Budget Changes"

    subscription_id = fields.Many2one("sale.subscription", string="Subscription")
    subscription_href = fields.Char(string="Subscription Link", compute="_get_subscription_href")
    report_href = fields.Char(string="Report Link", compute="_get_report_href")
    partner_id = fields.Many2one("res.partner", string="Client")
    product_id = fields.Many2one("product.product", string="Product")
    product_description = fields.Char(string="Product Description")
    category_id = fields.Many2one(
        "product.category", related="product_id.categ_id", store=True, readonly=True, string="Category"
    )
    price_full = fields.Float(string="New Budget")
    change_date = fields.Date(sting="New Start Date")
    change_price = fields.Float(string="New Budget Change")
    change_wholesale = fields.Float(string="New Wholesale")
    change_mngmt_fee = fields.Float(string="New Management Fee")
    prev_date = fields.Date(sting="Previous Change Date")
    prev_price = fields.Float(string="Previous Retail Price")
    prev_wholesale = fields.Float(string="Previous Wholesale")
    next_date = fields.Date(sting="Next Budget Change Date")
    next_price = fields.Float(string="Next Budget Change Price")
    next_wholesale = fields.Float(string="Next Budget Change Wholesale")
    status = fields.Selection([("new", "New"), ("completed", "Completed")], string="Status", default="new")
    completed_date = fields.Date(sting="Completion Date", default=None)

    def write(self, vals):
        # updating the completed data field with current date
        if "status" in vals and vals["status"] == "completed":
            self.completed_date = fields.Date.today()

        return super().write(vals)

    def _get_subscription_href(self):
        web_base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for element in self:
            element.subscription_href = (
                web_base_url
                + "/web#action=433&active_id=65551&id=%s&model=sale.subscription&view_type=form"
                % (element.subscription_id.id)
            )

    def _get_report_href(self):
        web_base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for element in self:
            element.report_href = web_base_url + "/budget_report/%s" % (element.partner_id.id)

    def complete_budget_changes(self):
        for change in self:
            change.update({"status": "completed"})

    def refresh_changes(self, changed_line):
        date_signature = "%Y-%m-%d"

        # mutate the table depending on new/change of price
        def process_change(change_dates_existing, date, change, start_period_date, subscription):
            signature = date + "|" + str(subscription.id)
            if signature in change_dates_existing:
                change_dates_existing[signature]["change_price"] += change
            else:
                change_dates_existing[signature] = {
                    "change_price": change,
                    "start_period_date": start_period_date.strftime(date_signature),
                    "subscription": subscription,
                }

        subscription = changed_line.analytic_account_id
        current_product = subscription.product_id
        partner_id = subscription.partner_id
        all_subscriptions = [subscription]

        # collecting the related products from product mapping table
        products_related = self.env["sale.budget.product.map"].search(
            ["|", ("product_1_id", "=", current_product.id), ("product_2_id", "=", current_product.id)], limit=1
        )
        main_product = products_related.product_1_id

        if products_related:
            if current_product == products_related.product_1_id:
                secondary_product = products_related.product_2_id
            else:
                secondary_product = products_related.product_1_id
            subscription_secondary = list(
                filter(
                    lambda x: x.product_id == secondary_product,
                    self.env["sale.subscription"].search(
                        [
                            ("partner_id.id", "=", partner_id.id),
                            ("is_active", "=", True),
                        ]
                    ),
                )
            )

            # if we have more than one active subscription for "linked" product - do nothing as this should never happen
            if len(subscription_secondary) > 1:
                self.env["bus.bus"].sendone(
                    (self._cr.dbname, "sale.subscriptions", self.env.user.partner_id.id),
                    {
                        "type": "snailmail_invalid_address",
                        "title": "Error in settings",
                        "message": "More than one linked product subscription found. This should not happen. Please, inform the developer regarding this.",
                        "sticky": True,
                    },
                )
                return
            if len(subscription_secondary) == 1:
                all_subscriptions += [subscription_secondary[0]]

        budget_changes_domain = [("subscription_id.id", "in", list(map(lambda x: x.id, all_subscriptions)))]

        change_dates_existing = {}
        change_dates_existing_processed = {}
        change_dates_to_update = {}
        periods_spending = {}

        # getting existing changes
        current_changes = self.search(budget_changes_domain)

        # collect data for existing Budget Change items
        for line in current_changes:
            line_change_date_text = line.change_date.strftime(date_signature)
            if line.status == "completed":
                if line_change_date_text not in change_dates_existing_processed:
                    change_dates_existing_processed[line_change_date_text] = line
                else:
                    if line.completed_date > change_dates_existing_processed[line_change_date_text].completed_date:
                        change_dates_existing_processed[line_change_date_text] = line
            else:
                if line_change_date_text not in change_dates_existing:
                    change_dates_existing[line_change_date_text] = line

        product_id = subscription.product_id
        involved_periods = {}
        # todo: possible optimization regarding filter out the old subscription lines
        # processing the subscription lines to collect spending/changing data
        # treating all lines from all subsriptions as same product. price details will be calculated lated based on
        # product pricelist
        for subscription_iterator in all_subscriptions:
            for line in subscription_iterator.recurring_invoice_line_ids:
                start_period_date = line.start_date.replace(day=1)
                start_period_date_text = start_period_date.strftime(date_signature)

                # generating the changes data
                #   starting period
                start_period_date = line.start_date.replace(day=1)
                start_date_text = line.start_date.strftime(date_signature)
                zero_spending = {"wholesale": 0, "management_fee": 0, "price_full": 0}
                if line["prorate_amount"] != 0:
                    next_period_start = start_period_date + relativedelta(months=1)
                    next_period_start_text = next_period_start.strftime(date_signature)
                    process_change(
                        change_dates_to_update,
                        start_date_text,
                        line["prorate_amount"],
                        start_period_date,
                        subscription_iterator,
                    )
                    process_change(
                        change_dates_to_update,
                        next_period_start_text,
                        line["price_unit"] - line["prorate_amount"],
                        next_period_start,
                        subscription_iterator,
                    )
                    if next_period_start_text not in involved_periods:
                        involved_periods[next_period_start_text] = next_period_start

                else:
                    process_change(
                        change_dates_to_update,
                        start_date_text,
                        line["price_unit"],
                        start_period_date,
                        subscription_iterator,
                    )

                if start_period_date_text not in involved_periods:
                    involved_periods[start_period_date_text] = start_period_date

                if line.end_date:
                    start_next_period_date = line.end_date + relativedelta(days=1)
                    start_next_period_date_text = start_next_period_date.strftime(date_signature)
                    #   ending period
                    if line["prorate_end_amount"] != 0:
                        start_last_month_service = line.end_date.replace(day=1)
                        start_last_month_service_text = start_last_month_service.strftime(date_signature)
                        process_change(
                            change_dates_to_update,
                            start_last_month_service_text,
                            line["prorate_end_amount"] - line["price_unit"],
                            start_last_month_service,
                            subscription_iterator,
                        )
                        process_change(
                            change_dates_to_update,
                            start_next_period_date_text,
                            -line["prorate_end_amount"],
                            start_next_period_date,
                            subscription_iterator,
                        )
                        if start_last_month_service_text not in involved_periods:
                            involved_periods[start_last_month_service_text] = start_last_month_service
                    else:
                        process_change(
                            change_dates_to_update,
                            start_next_period_date_text,
                            -line["price_unit"],
                            start_next_period_date.replace(day=1),
                            subscription_iterator,
                        )

                    if start_next_period_date_text not in involved_periods:
                        involved_periods[start_next_period_date_text] = start_next_period_date

        # pricelist_product = subscription.pricelist_determination(product_id, subscription.pricelist_id)

        pricelist = {}
        for subscription_iterator in all_subscriptions:
            pricelist[subscription_iterator.id] = subscription_iterator.pricelist_determination(
                subscription_iterator.product_id, subscription_iterator.pricelist_id
            )
            for line in subscription_iterator.recurring_invoice_line_ids:
                for period_process in involved_periods:
                    period_process_signature = period_process + "|" + str(subscription_iterator.id)
                    if period_process_signature in periods_spending:
                        periods_spending[period_process_signature]["price_full"] += line.period_price_calc(
                            involved_periods[period_process], partner_id, True
                        )
                    else:
                        periods_spending[period_process_signature] = {
                            "price_full": line.period_price_calc(involved_periods[period_process], partner_id, True),
                            "date": involved_periods[period_process],
                        }

        # calc wholesale and management fee for periods with changes.
        for period in periods_spending:
            price_including_middlemonth_changes = periods_spending[period]["price_full"]
            [period_current, pricelist_current] = period.split("|")
            additional_data = subscription.subscription_wholesale_period(
                price_including_middlemonth_changes, pricelist[int(pricelist_current)]
            )
            periods_spending[period].update(
                {
                    "management_fee": additional_data["management_fee"],
                    "wholesale": additional_data["wholesale_price"],
                }
            )

        # combining all subscriptions to total monthly spending
        periods_spending_combined = {}
        for period in periods_spending:
            [period_current, pricelist_current] = period.split("|")
            if period_current in periods_spending_combined:
                periods_spending_combined[period_current]["price_full"] += periods_spending[period]["price_full"]
                periods_spending_combined[period_current]["wholesale"] += periods_spending[period]["wholesale"]
                periods_spending_combined[period_current]["management_fee"] += periods_spending[period][
                    "management_fee"
                ]
            else:
                periods_spending_combined[period_current] = periods_spending[period]

        # combining all subscriptions to total monthly spending
        change_dates_to_update_combined = {}
        for period in change_dates_to_update:
            [period_current, pricelist_current] = period.split("|")
            if period_current in change_dates_to_update_combined:
                if change_dates_to_update_combined[period_current]["change_price"] < change_dates_to_update[period]["change_price"]:
                    change_dates_to_update_combined[period_current]['subscription'] = change_dates_to_update[period]["subscription"]
                change_dates_to_update_combined[period_current]["change_price"] += change_dates_to_update[period][
                    "change_price"
                ]
            else:
                change_dates_to_update_combined[period_current] = change_dates_to_update[period]

        # comparing changes
        sorted_dates = sorted(list(periods_spending_combined.keys()))

        # remove changes having the same spending
        for i in range(len(sorted_dates) - 1, 0, -1):
            if change_dates_to_update_combined[sorted_dates[i]]["change_price"] == 0:
                del change_dates_to_update_combined[sorted_dates[i]]
                del sorted_dates[i]

        # clean up existing changes
        for change_date in change_dates_existing:
            if change_date not in sorted_dates:
                change_dates_existing[change_date].unlink()

        # Initial  date need to be passed as Ops team won't have notification about it.
        # So scan till index 0 excluding
        for change_date_idx in range(len(sorted_dates) - 1, 0, -1):
            change_date = sorted_dates[change_date_idx]
            processing_change = change_dates_to_update_combined[change_date]
            # filter out changes happened before August 2021
            if datetime.datetime.strptime(change_date, date_signature) < datetime.datetime(2021, 8, 1):
                continue
            prev_date = sorted_dates[change_date_idx - 1]

            # generate the change object
            period_start_date = processing_change["start_period_date"]
            money_detils = (
                zero_spending
                if period_start_date not in periods_spending_combined
                else periods_spending_combined[period_start_date]
            )

            prev_money_detils = (
                zero_spending if prev_date not in periods_spending_combined else periods_spending_combined[prev_date]
            )

            next_date = False
            next_money_details = zero_spending
            if (change_date_idx + 1) < len(sorted_dates):
                next_date = sorted_dates[change_date_idx + 1]
                if next_date in periods_spending_combined:
                    next_money_details = periods_spending_combined[next_date]
            management_fee = money_detils["management_fee"] if money_detils["management_fee"] >= 0 else 0.0
            change_object = {
                "partner_id": partner_id.id,
                "subscription_id": subscription.id,
                "product_id": product_id.id,
                "product_description": subscription.description,
                "change_date": datetime.datetime.strptime(change_date, date_signature),
                "change_price": processing_change["change_price"],
                "price_full": money_detils["price_full"],
                "change_wholesale": money_detils["wholesale"],
                "change_mngmt_fee": management_fee,
                "prev_date": datetime.datetime.strptime(prev_date, date_signature),
                "prev_price": prev_money_detils["price_full"],
                "prev_wholesale": prev_money_detils["wholesale"],
                "next_date": next_date,
                "next_price": next_money_details["price_full"],
                "next_wholesale": next_money_details["wholesale"],
            }

            # if checking date already exist
            if change_date in change_dates_existing and not (
                change_date in change_dates_existing_processed
                and change_dates_existing_processed[change_date]["change_price"]
                == change_dates_existing[change_date]["change_price"]
                and change_dates_existing_processed[change_date]["total_price"]
                == change_dates_existing[change_date]["total_price"]
            ):

                # if change_dates_existing[change_date]["change_price"] != processing_change["change_price"] or change_dates_existing[change_date]["price_full"] != processing_change["price_full"]:
                #     if (
                #         prev_date in change_dates_existing
                #         and change_date in change_dates_existing
                #         and change_dates_existing[change_date]["change_price"]
                #         == change_dates_existing[prev_date]["change_price"]
                #     ):
                #         # if prefious changes is same as current one - delete the existing
                #         self.delete(change_dates_existing[change_date].id)
                # else:
                change_dates_existing[change_date].update(change_object)
            else:
                self.create(change_object)

    def call_the_report(self):
        # action = self.env.ref("clx_budget_analysis_report.action_budget_report_wizard").read()[0]
        # budget_report_object = self.env.ref("clx_budget_analysis_report.sale_budget_report_action").read()[0]
        context = self._context
        partner_id = self.browse(context["default_client_id"]).id
        report = self.env["budget.report.wizard"].create(
            {
                "partner_ids": [partner_id],
                "start_date": (datetime.datetime.today().replace(day=1) + relativedelta(months=-2)),
                "end_date": (datetime.datetime.today().replace(day=1) + relativedelta(months=+2, days=-1)),
            }
        )
        return report.with_context({"action_next": "sale_budget_report_action_qweb"}).get_budget_report()
