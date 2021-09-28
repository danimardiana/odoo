# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from collections import OrderedDict
from datetime import timedelta, date


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    def create_invoices(self):
        sale_order_id = self._context.get("active_id", False)
        if not sale_order_id:
            raise UserError(_("You need to sale order for create a invoice!!"))
        sale_order = self.env["sale.order"].browse(sale_order_id)
        start_date = self.start_date
        end_date = self.end_date
        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = date.today() + relativedelta(months=sale_order.partner_id.clx_invoice_policy_id.num_of_month + 1)

        self.env["sale.subscription"].invoicing_invoice_policy_range(
            **{
                "partner_id": sale_order.partner_id.id,
                "partner": sale_order.partner_id,
                "order_id": sale_order_id,
            }
        )
        if self._context.get("open_invoices", False):
            return sale_order.action_view_invoice()

        return