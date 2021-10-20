# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import models, fields

from dateutil import parser
from datetime import timedelta
from collections import OrderedDict


class Invoice(models.Model):
    _inherit = "account.move"

    def regroup_lines_for_preview(self):
        def _grouping_name_calc(line, partner_id):
            # partner_id = line.so_line_id.order_id.partner_id
            product_id = line["product_id"]
            description = product_id.categ_id.name
            if partner_id.invoice_selection == "sol":
                description = self.env["sale.order.line"]._grouping_by_product_logic(
                    product_id, partner_id, line["name"]
                )
            return description

        invoice_lines = []
        for line in self.invoice_line_ids:
            invoice_lines.append(
                {
                    "name": line.product_id.name,
                    "product_name": line.product_id.name,
                    "product_id": line.product_id,
                    "product_variant": line.product_id.product_template_attribute_value_ids.name or "",
                    "category_name": line.category_id.name,
                    "category_id": line.category_id,
                    "price_subtotal": line.price_subtotal,
                    "price_total": line.price_total,
                    "discount": line.discount,
                    "description": line.description,
                    "tax_ids": line.tax_ids,
                }
            )
        # grouping by accounting wrapping rules (product level, "Budget Wrapping" fields )
        for line in invoice_lines:
            line["description"] = _grouping_name_calc(line, self.partner_id)

        # grouping by products set
        self.env["sale.order"].grouping_by_product_set(invoice_lines)

        grouped_lines = {}

        for product_individual in invoice_lines:
            # combine the lines contains the same description, tax and discount
            combined_signature = (
                product_individual["description"]
                + ",".join(map(lambda tax: str(tax), product_individual["tax_ids"]))
                + str(product_individual["discount"])
            )

            if combined_signature in grouped_lines:
                grouped_lines[combined_signature]["price_subtotal"] += product_individual["price_subtotal"]
                grouped_lines[combined_signature]["price_total"] += product_individual["price_total"]
                grouped_lines[combined_signature]["discount"] += product_individual["discount"]
            else:
                grouped_lines[combined_signature] = product_individual

        return list(grouped_lines.values())

    def print_date(self, inv_line):
        month = " "
        temp = []
        inv_line_unique = []
        for line in list(set(inv_line.mapped("name"))):
            if "Invoicing period" in line:
                inv_line_unique.append(line)
        if inv_line_unique:
            name = inv_line_unique[0].split(":")
            name = name[-1].split("-")
            start_date = parser.parse(name[0])
            end_date = inv_line_unique[-1].split(":")
            end_date = end_date[-1].split("-")
            end_date = parser.parse(end_date[-1])
            months = OrderedDict(
                ((start_date + timedelta(_)).strftime("%B-%Y"), 0) for _ in range((end_date - start_date).days)
            )

            temp = list(months)
            for i in temp:
                if "December" not in i:
                    month += i.split("-")[0] + ","
                else:
                    month += " " + i + ","
            if len(months) == 1:
                month = list(months)[0]
            # if month and temp:
            #     month += '-' + temp[-1].split('-')[-1] + ' '
            #     month = month.replace(',-' + temp[-1].split('-')[-1], '-' + temp[-1].split('-')[-1])
        return month
