# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, models, api
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
from datetime import timedelta
from calendar import monthrange, month_name
from . import grouping_data


class BudgetReportWizard(models.TransientModel):
    _name = "budget.report.wizard"
    _description = "Budget Report Wizard"

    partner_ids = fields.Many2many("res.partner", string="Customers")
    start_date = fields.Date(
        string="Start Date",
        default=fields.Date.today().replace(day=1) + relativedelta(months=-3),
    )
    end_date = fields.Date(
        string="End Date",
        default=fields.Date.today().replace(day=1) + relativedelta(days=-1, months=4),
    )

    def reset(self):
        self.partner_ids = False
        action = self.env.ref("clx_budget_analysis_report.action_budget_report_wizard").read()[0]
        return action

    @api.model
    def default_get(self, fields):
        result = super(BudgetReportWizard, self).default_get(fields)
        wizard_records = self.search([], order="id DESC")
        if wizard_records:
            result.update(
                {
                    "partner_ids": wizard_records[0].partner_ids.ids,
                    "start_date": wizard_records[0].start_date,
                    "end_date": wizard_records[0].end_date,
                }
            )
        return result

    # the grouping specfic for budget report: no grouping of any kind except
    # the subscription lines belong to same subscription
    def _grouping_wrapper(self, **kwargs):

        start_date = kwargs.get("start_date", False)
        partner_id = kwargs.get("partner_id", False)
        subscripion_line = kwargs.get("subscripion_line", False)
        grouping_levels = kwargs.get("grouping_levels", 16)
        is_root = kwargs.get("is_root", False)
        if not subscripion_line or not start_date:
            return {}

        def initial_order_data(line, partner_id):
            price, price_full, coop_coef = line.period_price_calc(start_date, partner_id, is_root)
            product_variant = ""
            if len(line.product_id.product_template_attribute_value_ids):
                product_variant = line.product_id.product_template_attribute_value_ids[0].name
            rebate, rebate_product = line.rebate_calc(price)
            pricelist2process = line.analytic_account_id.pricelist_determination(
                line.product_id, line.analytic_account_id.pricelist_id
            )
            start_date_final = kwargs["start_date"] if kwargs["start_date"] > line.start_date else line.start_date
            end_date_final = kwargs.get("end_date", start_date + relativedelta(days=-1, months=1))
            end_date_final = line.end_date if line.end_date and end_date_final > line.end_date else end_date_final
            return {
                "id": line.id,
                "product_name": line.product_id.name,
                "product_variant": product_variant,
                "partner_owner": line.analytic_account_id.partner_id,
                "product_id": line.product_id.id,
                "coop_coef": coop_coef,
                "product_variant": line.product_id.product_template_attribute_value_ids.name or "",
                "name": line.name,
                "subscription_id": line.analytic_account_id.id,
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
                "description": line.name,
                "contract_product_description": line.product_id.contract_product_description,
                "rebate": rebate,
                # "rebate_product": rebate_product,
                "discount": line.discount,
                "tax_ids": list(map(lambda tax: tax.id, line.so_line_id.tax_id)),
                "start_date": start_date_final,
                "end_date": end_date_final,
            }

        # just filtering the fields necessary for last step - invoice creation
        def last_order_data(product_individual):
            return {
                "id": product_individual["id"],
                "subscription_id": product_individual["subscription_id"],
                "coop_coef": product_individual["coop_coef"],
                "product_name": product_individual["product_name"],
                "product_variant": product_individual["product_variant"],
                "price_unit": product_individual["price_unit"],
                "description": product_individual["description"],
                "contract_product_description": product_individual["contract_product_description"],
                "account_id": product_individual["account_id"],
                "name": product_individual["name"],
                "category_id": product_individual["category_id"],
                "product_id": product_individual["product_id"],
                "partner_owner": product_individual["partner_owner"],
                "pricelist": product_individual["pricelist"],
                "price_full": product_individual["price_full"],
                "wholesale_price": product_individual["wholesale_price"],
                "start_date": product_individual["start_date"],
                "end_date": product_individual["end_date"],
                "management_fee": product_individual["management_fee"],
                "management_fee_product": product_individual["management_fee_product"],
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
            # product_updated["rebate"] += product_additional["rebate"]
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

        source_lines = subscripion_line
        return self.env["sale.order"].grouping_all_products(
            source_lines,
            partner_id,
            initial_order_data,
            last_order_data,
            last_order_update,
            start_date,
            grouping_levels,
        )

    def get_budget_report(self):
        # clean up the previous report data
        self._cr.execute("DELETE FROM sale_subscription_report_data")
        report_data_table = self.env["sale.subscription.report.data"]
        params = self.env["ir.config_parameter"].sudo()

        def get_all_sublines(partner_ids):
            # search all subscriptions lines for the client
            return self.env["sale.subscription.line"].search(
                [
                    "|",
                    ("analytic_account_id.co_op_partner_ids.partner_id", "in", partner_ids),
                    ("analytic_account_id.partner_id", "in", partner_ids),
                    ("start_date", "!=", False),
                    "|",
                    ("end_date", ">=", self.start_date),
                    ("end_date", "=", False),
                    ("start_date", "<=", self.end_date),
                ],
                order="start_date asc",
            )

        slider_start_date = self.start_date.replace(day=1)
        slider_end_date = self.start_date.replace(day=monthrange(slider_start_date.year, slider_start_date.month)[1])
        slider_period = month_name[slider_start_date.month] + " " + str(slider_start_date.year)

        periods_list = [(slider_start_date, slider_end_date, slider_period)]
        while True:
            slider_start_date = slider_start_date + relativedelta(months=1)
            slider_end_date = slider_start_date.replace(
                day=monthrange(slider_start_date.year, slider_start_date.month)[1]
            )
            slider_period = month_name[slider_start_date.month] + " " + str(slider_start_date.year)
            periods_list.append((slider_start_date, slider_end_date, slider_period))
            if slider_end_date > self.end_date:
                break
        related_companies = list()

        def process_clients_for_period(partners_ids, subscription_lines, is_root):
            # period_slist and result_table are global for this
            for partner_id_int in partners_ids:
                partner_id = self.env["res.partner"].browse(partner_id_int)
                subscription_lines_set_for_partner = list(
                    filter(
                        lambda l: l.analytic_account_id.partner_id.id == partner_id_int
                        or partner_id_int in l.analytic_account_id.co_op_partner_ids.mapped("partner_id").mapped("id"),
                        subscription_lines,
                    )
                )
                for period in periods_list:
                    slider_start_date, slider_end_date, slider_period = period
                    for sub_line in subscription_lines_set_for_partner:
                        for co_op_line in sub_line.analytic_account_id.co_op_partner_ids:
                            if co_op_line.partner_id.id not in related_companies:
                                related_companies.append(co_op_line.partner_id.id)
                    # don't do grouping of any kind, as OPS need to has link to each subscription
                    global_grouped_sub_lines = self._grouping_wrapper(
                        start_date=slider_start_date,
                        end_date=slider_end_date,
                        partner_id=partner_id,
                        subscripion_line=subscription_lines_set_for_partner,
                        grouping_levels=grouping_data.SUBSCRIPTION_GROUPING_FLAG,
                        is_root=is_root,
                    )

                    for sub_line in global_grouped_sub_lines.values():
                        if sub_line["price_unit"] == 0:
                            continue
                        sub_line["description"] += (
                            "" if sub_line["coop_coef"] == 1.0 else " (%s%%) " % (str(int(sub_line["coop_coef"] * 100)))
                        )
                        subscribtion_total = {
                            "id": sub_line["id"],
                            "period": slider_period,
                            "start_date": sub_line["start_date"],
                            "product_id": sub_line["product_id"],
                            "subscription_line_id": sub_line["id"],
                            "partner_id": partner_id_int,
                            "end_date": sub_line["end_date"],
                            "subscription_id": sub_line["subscription_id"],
                            "price_unit": sub_line["price_unit"] * sub_line["coop_coef"],
                            "description": sub_line["description"],
                            "category_id": sub_line["category_id"],
                            "management_fee": sub_line["management_fee"] * sub_line["coop_coef"],
                            "wholesale_price": sub_line["wholesale_price"] * sub_line["coop_coef"],
                            "company_name": partner_id.name,
                        }
                        report_data_table.create(subscribtion_total)

        all_sublines = get_all_sublines(self.partner_ids.ids)
        process_clients_for_period(self.partner_ids.ids, all_sublines, True)
        # adding co-ops companies to report
        all_sublines = get_all_sublines(related_companies)
        process_clients_for_period(related_companies, all_sublines, False)

        action = self.env.ref("clx_budget_analysis_report." + self.env.context["action_next"]).read()[0]

        return action


class qweb_sale_subscription_budgets_report(models.AbstractModel):
    _name = "report.clx_budget_analysis_report.report_budget_qweb"

    @api.model
    def _get_report_values(self, docids, data=None):
        report_obj = self.env["ir.actions.report"]
        report = report_obj._get_report_from_name("sale_subscription.budgets_report")
        subscriptions = self.env["sale.subscription.report.data"].search([])
        subscriptions_gouped = {}
        all_periods = []
        for subscription in subscriptions:
            if subscription.partner_id.id not in subscriptions_gouped:
                subscriptions_gouped[subscription.partner_id.id] = {
                    "partner_id": subscription.partner_id.id,
                    "company_name": subscription.company_name,
                }

            if "subs" not in subscriptions_gouped[subscription.partner_id.id]:
                subscriptions_gouped[subscription.partner_id.id]["subs"] = {}

            if subscription.subscription_id.id not in subscriptions_gouped[subscription.partner_id.id]["subs"]:
                subscriptions_gouped[subscription.partner_id.id]["subs"][subscription.subscription_id.id] = {
                    "description": subscription.description,
                    "subscription_id": subscription.subscription_id.id,
                }

            if (
                subscription.period
                not in subscriptions_gouped[subscription.partner_id.id]["subs"][subscription.subscription_id.id]
            ):
                subscriptions_gouped[subscription.partner_id.id]["subs"][subscription.subscription_id.id][
                    subscription.period
                ] = []
                if subscription.period not in all_periods:
                    all_periods.append(subscription.period)

            subscriptions_gouped[subscription.partner_id.id]["subs"][subscription.subscription_id.id][
                subscription.period
            ].append(
                {
                    "price_unit": subscription.price_unit,
                    "wholesale_price": subscription.wholesale_price,
                    "management_fee": subscription.management_fee,
                    "management_fee_product": subscription.management_fee_product,
                    "start_date": subscription.start_date,
                    "end_date": subscription.end_date,
                }
            )
        group_sales = self.env["res.groups"].search([("name", "=", "CLX Sale Group")])
        fees_allowed = self.env.user.id not in group_sales.users.ids
        docargs = {
            "doc_ids": docids,
            "doc_model": report.model,
            "docs": self,
            "all_periods": all_periods,
            "companies": subscriptions_gouped,
            "get_all": self.get_all,
            "fees_allowed": fees_allowed,
            # 'print_data': self.print_data,
            # 'get_qty_done_sum': self.get_qty_done_sum,
        }
        return docargs

    @api.model
    def get_all(self):
        data = self._cr.execute(
            """SELECT sbl.id,sbl.start_date as start_date,
            sbl.product_id as product_id,
            sbl.subscription_id as subscription_id,
            sbl.subscription_line_id as subscription_line_id,
            sbl.management_fee as management_fee,
            sbl.management_fee_product as management_fee_poduct,
            sbl.partner_id as partner_id,
            sbl.wholesale_price as wholesale_price,
            sbl.price_unit as price,
            sbl.end_date as end_date
            from sale_subscription_report_data AS sbl group by sbl.partner_id,sbl.id"""
        )
        result = self._cr.fetchall()
        return result


class sale_subscription_budgets_report(models.AbstractModel):
    _name = "report.sale_subscription.budgets_report"

    @api.model
    def get_html(self, docids, data=None):
        report_obj = self.env["ir.actions.report"]
        report = report_obj._get_report_from_name("sale_subscription.budgets_report")
        spk = self.env["sale.subscription.report.data"].search([("id", "=", docids)])
        docargs = {
            "doc_ids": docids,
            "doc_model": report.model,
            "docs": self,
            "spk": spk,
            "get_all": self.get_all,
            "print_data": self.print_data,
            "get_qty_done_sum": self.get_qty_done_sum,
        }
        return report_obj.render("sale_reports.report_sale_order_subscription_lines", docargs)

    def get_all(self, para):
        self._cr.execute(
            """SELECT sbl.id,sbl.start_date as start_date,
            sbl.product_id as product_id,
            sbl.subscription_id as subscription_id,
            sbl.management_fee as management_fee,
            sbl.partner_id as partner_id,
            sbl.wholesale_price as wholesale_price,
            sbl.price_unit as price_unit,
            sbl.period as period
            sbl.end_date as end_date
            from sale_subscription_report_data AS sbl group by sbl.partner_id,sbl.id"""
            % (para, para)
        )

    def print_data(self, para):
        dict = {}
        list = []
        return list

    def get_qty_done_sum(self, para):

        self._cr.execute(
            """\
                select sum(retail) from sale_subscription_report_data 
                """
            % para
        )
        return self._cr.fetchall()
