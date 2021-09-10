# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
# Model for parameters request
import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from odoo import fields, models, api, _
import base64
import io
import xlsxwriter
import time

REPORT_STRUCTURE = [
    {
        "header": "Company ID",
        "report_column": 0,
        "field_name": "partner_id",
    },
    {
        "header": "Company Name",
        "report_column": 1,
        "field_name": "company_name",
    },
    {
        "header": "Vertical",
        "report_column": 2,
        "field_name": "vertical",
    },
    {
        "header": "Product Category",
        "report_column": 3,
        "field_name": "category",
    },
    {
        "header": "Product Name",
        "report_column": 4,
        "field_name": "product_name",
    },
    {
        "header": "Product Variant",
        "report_column": 5,
        "field_name": "product_variant",
    },
    {
        "header": "Product Description",
        "report_column": 6,
        "field_name": "description",
    },
    {
        "header": "Retail",
        "report_column": 7,
        "field_name": "retail",
    },
    {
        "header": "Wholesale",
        "report_column": 8,
        "field_name": "wholesale",
    },
    {
        "header": "Management Fee",
        "report_column": 9,
        "field_name": "management_fee",
    },
    {
        "header": "Start Date",
        "report_column": 10,
        "field_name": "start_date",
    },
    {
        "header": "End Date",
        "report_column": 11,
        "field_name": "end_date",
    },
    {
        "header": "Google ID",
        "report_column": 12,
        "field_name": "google_id",
    },
    {
        "header": "FB ID",
        "report_column": 13,
        "field_name": "fb_id",
    },
]


class SaleBudgetExports(models.TransientModel):
    _name = "sale.budget.export.wizard"
    _description = "Sale Budget Export Parameters"

    start_date = fields.Date(
        string="Start Date",
        default=fields.Date.today().replace(day=1),
    )
    end_date = fields.Date(
        string="End Date",
        default=fields.Date.today().replace(day=1) + relativedelta(days=-1, months=1),
    )

    @api.onchange("start_date", "end_date")
    def onchange_date_validation(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError(_("Invalid date range."))

    # for now it's just exporting data generation
    def collect_report_data(self):
        subscription_object = self.env["sale.subscription"]
        subscription_line_object = self.env["sale.subscription.line"]

        return_data = []

        query = """SELECT ssl.id, sl.partner_id FROM sale_subscription_line as ssl 
        inner join  sale_subscription as sl on sl.id=ssl.analytic_account_id
        where ssl.start_date<='%s' 
        and (ssl.end_date >= '%s' or ssl.end_date is NULL)""" % (
            self.end_date,
            self.start_date,
        )
        self.env.cr.execute(query)
        all_subscriptions = self.env.cr.fetchall()
        all_odoo_partners = {}

        # combining subscriptions by partners
        for subscription in all_subscriptions:
            (
                subline_id,
                partner_id,
            ) = subscription
            if partner_id in all_odoo_partners:
                all_odoo_partners[partner_id] += [subline_id]
            else:
                all_odoo_partners[partner_id] = [subline_id]

        for partner_id in all_odoo_partners:

            subscription_lines = subscription_line_object.browse(all_odoo_partners[partner_id])

            all_subscriptions = subscription_object._grouping_wrapper(
                self.start_date, partner_id, subscription_lines, 5
            )

            for subscription in all_subscriptions:
                wholesale = subscription["wholesale_price"]
                if wholesale <= 0 and subscription["management_fee"] > 0:
                    wholesale = subscription["price_unit"] - subscription["management_fee"]
                start_date = (
                    self.start_date
                    if not subscription["start_date"] or self.start_date > subscription["start_date"]
                    else subscription["start_date"]
                )
                end_date = (
                    self.end_date
                    if not subscription["end_date"] or self.end_date < subscription["end_date"]
                    else subscription["end_date"]
                )
                partner_object = self.env["res.partner"].browse(partner_id)
                return_object = {
                    "partner_id": partner_id,
                    "company_name": partner_object.name,
                    "vertical": partner_object.vertical,
                    "retail": subscription["price_unit"],
                    "category": self.env["product.category"].browse(subscription["category_id"]).name,
                    "product_name": subscription["product_name"],
                    "product_variant": subscription["product_variant"],
                    "management_fee": "" if subscription["management_fee"]<=0 else subscription["management_fee"],
                    "wholesale": "" if wholesale<=0 else wholesale,
                    "description": subscription["description"],
                    "start_date": start_date.strftime("%m/%d/%Y"),
                    "end_date": end_date.strftime("%m/%d/%Y"),
                    "google_id": "" if not partner_object.google_ads_account else partner_object.google_ads_account,
                    "fb_id":  "" if not partner_object.fb_account else partner_object.fb_account,
                }
                return_data.append(list(map(lambda x: return_object[x["field_name"]], REPORT_STRUCTURE)))

        return return_data

    def download_report(self):
        all_data = self.collect_report_data()

        fp = io.BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        worksheet = workbook.add_worksheet("Budgeting")
        header_format = workbook.add_format({"bold": True})

        for col in REPORT_STRUCTURE:
            worksheet.write(0, col["report_column"], col["header"], header_format)

        for idx, line in enumerate(all_data):
            worksheet.write_row(idx + 1,0, line)

        workbook.close()
        fp.seek(0)
        result = base64.b64encode(fp.read())
        attachment_obj = self.env["ir.attachment"]
        attachment_id = attachment_obj.create(
            {"name": "budget_report_%s.xlsx"%(self.start_date.strftime("%m/%d/%Y")), "display_name": "udget ReBport %s.xlsx"%(self.start_date.strftime("%m/%d/%Y")), "datas": result}
        )
        download_url = "/web/content/" + str(attachment_id.id) + "?download=True"

        return {
            "type": "ir.actions.act_url",
            "url": str(download_url),
            "target": "new",
            "nodestroy": False,
        }