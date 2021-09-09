# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, models, api
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
from datetime import timedelta
from calendar import monthrange, month_name
import datetime
import json


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

    def get_budget_report(self):
        # clean up the previous report data
        self._cr.execute("DELETE FROM sale_subscription_report_data")
        report_data_table = self.env["sale.subscription.report.data"]
        params = self.env["ir.config_parameter"].sudo()
        # search all subscriptions lines for the client
        # TODO: update with co-op information
        subscription_lines = self.env["sale.subscription.line"].search(
            [
                "|",
                # "&",
                # !!! COOP rebuild
                # ("analytic_account_id.is_co_op", "=", True),
                # ("analytic_account_id.co_opp_partner_ids.partner_id", "in", self.partner_ids.ids),
                ("analytic_account_id.co_op_partner_ids.partner_id", "in", self.partner_ids.ids),
                ("analytic_account_id.partner_id", "in", self.partner_ids.ids),
                ("start_date", "!=", False),
                # ('product_id.subscription_template_id.recurring_rule_type', '=', 'monthly'),
                "|",
                ("end_date", ">=", self.start_date),
                ("end_date", "=", False),
                ("start_date", "<=", self.end_date),
            ],
            order="start_date asc",
        )
        if not len(subscription_lines):
            return
        slider_start_date = self.start_date.replace(day=1)
        slider_end_date = self.start_date.replace(day=monthrange(slider_start_date.year, slider_start_date.month)[1])
        slider_period = month_name[slider_start_date.month] + " " + str(slider_start_date.year)
        result_table = {}
        price_list = {}
        price_list_processed = []
        # partner_id = self.env["res.partner"].browse(self.partner_ids.ids[0])
        companies_list = {}
        category_show_params = {}
        while True:
            result_table[slider_period] = {}
            for sub_line in subscription_lines:
                partner_id = sub_line.analytic_account_id.partner_id
                companies_list["%s|%s" % (str(partner_id.id), str(sub_line.analytic_account_id.id))] = {
                    "company": partner_id,
                    "percent": 1.0,
                }
                if len(sub_line.analytic_account_id.co_op_partner_ids):
                    for co_op_line in sub_line.analytic_account_id.co_op_partner_ids:
                        sub_company_signature = "%s|%s" % (
                            str(co_op_line.partner_id.id),
                            str(sub_line.analytic_account_id.id),
                        )
                        companies_list[sub_company_signature] = {
                            "company": co_op_line.partner_id,
                            "percent": co_op_line.ratio / 100,
                        }

                # check if our sub_line intersect with period and get full price for subscription based on main company
                retail_price = sub_line.period_price_calc(
                    slider_start_date, sub_line.so_line_id.order_id.partner_id.id, True
                )
                # just pass sub.line if no spending this month
                if not retail_price:
                    continue
                price_list_id = sub_line.so_line_id.order_id.pricelist_id

                product_stamp = (
                    str(sub_line.so_line_id.order_id.partner_id.id) + "_" + str(sub_line.analytic_account_id.id)
                )

                # pricelist needed to calculate wholesale only
                # if not price_list_id in price_list_processed:
                #     price_list.update(self.env["sale.subscription"].pricelist_flatten(price_list_id))
                #     price_list_processed.append(price_list_id)
                if product_stamp in result_table[slider_period]:
                    result_table[slider_period][product_stamp]["retail_price"] += retail_price
                else:
                    # tags = [
                    #     str(price_list_id.id) + "_0_" + str(sub_line.product_id.id),
                    #     str(price_list_id.id) + "_1_" + str(sub_line.product_id.product_tmpl_id.id),
                    #     str(price_list_id.id) + "_2_" + str(sub_line.product_id.categ_id.id),
                    #     str(price_list_id.id) + "_3",
                    #     list(price_list.keys())[0],
                    # ]
                    # for tag in tags:
                    #     if tag in price_list:
                    #         pricelist2process = price_list[tag]
                    #         break
                    pricelist2process = sub_line.analytic_account_id.pricelist_determination(
                        sub_line.product_id, price_list_id
                    )

                    result_start_date = (
                        slider_start_date if slider_start_date >= sub_line.start_date else sub_line.start_date
                    )
                    result_end_date = slider_start_date.replace(
                        day=monthrange(slider_start_date.year, slider_start_date.month)[1]
                    )
                    if sub_line.end_date and sub_line.end_date < result_end_date:
                        result_end_date = sub_line.end_date
                    result_table[slider_period][product_stamp] = {
                        "period": slider_period,
                        "start_date": result_start_date,
                        "product_id": sub_line.product_id.id,
                        "subscription_id": sub_line.analytic_account_id.id,
                        "subscription_line_id": sub_line.id,
                        "partner_id": sub_line.so_line_id.order_id.partner_id.id,
                        # will be calculated based on final amount later
                        "wholesale_price": pricelist2process,
                        "end_date": result_end_date,
                        "retail_price": retail_price,
                        "description": sub_line.so_line_id.name,
                        "category": sub_line.product_id.categ_id.id,
                        "company_name": sub_line.so_line_id.order_id.partner_id.name,
                    }
                    category_show_params[sub_line.product_id.categ_id.id] = {
                        "show_mgmnt_fee": sub_line.product_id.categ_id.management_fee,
                        "show_wholesale": sub_line.product_id.categ_id.wholesale,
                    }

            slider_start_date += relativedelta(months=1)
            slider_end_date = slider_start_date.replace(
                day=monthrange(slider_start_date.year, slider_start_date.month)[1]
            )
            slider_period = month_name[slider_start_date.month] + " " + str(slider_start_date.year)
            if slider_end_date > self.end_date:
                break
        # saving to the report table
        for period in result_table.keys():
            for subscription in result_table[period].keys():
                sale_line_write = result_table[period][subscription]

                management_fee_data = self.env["sale.subscription"].subscription_wholesale_period(
                    sale_line_write["retail_price"],
                    sale_line_write["wholesale_price"],
                    category_show_params[sale_line_write["category"]],
                )
                # if "management_fee_product" in management_fee_data:
                #     del management_fee_data["management_fee_product"]
                result_table[period][subscription].update(management_fee_data)

                # pass thru all the companies related to the subscription
                subscription_id = subscription.split("_")[1]
                subscription_related_list = list(
                    filter(lambda signature: signature.split("|")[1] == subscription_id, companies_list.keys())
                )
                for partner_line in subscription_related_list:
                    subscribtion_total = sale_line_write.copy()
                    partner_percent = companies_list[partner_line]["percent"]
                    company = companies_list[partner_line]["company"]
                    company_name = company.name
                    description = subscribtion_total["description"]
                    if partner_percent != 1.0:
                        description += " (%s%%) " % (str(int(partner_percent * 100)))
                    management_fee_product = (
                        False
                        if not sale_line_write["management_fee_product"]
                        or len(sale_line_write["management_fee_product"]) == 0
                        else sale_line_write["management_fee_product"].id
                    )
                    subscribtion_total.update(
                        {
                            "description": description,
                            "partner_id": company.id,
                            "wholesale_price": partner_percent * sale_line_write["wholesale_price"]
                            if (sale_line_write["wholesale_price"]) > 0
                            else sale_line_write["wholesale_price"],
                            "management_fee": partner_percent * sale_line_write["management_fee"]
                            if abs(sale_line_write["management_fee"]) > 0
                            else sale_line_write["management_fee"],
                            "retail_price": partner_percent * sale_line_write["retail_price"],
                            "company_name": company_name,
                            "management_fee_product": management_fee_product,
                        }
                    )
                    report_data_table.create(subscribtion_total)

        # action = self.env.ref(
        #     'clx_budget_analysis_report.'+self.env.context['action_next']).read()[0]

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
                    "retail_price": subscription.retail_price,
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
            sbl.retail_price as price,
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
            sbl.retail_price as retail_price,
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
