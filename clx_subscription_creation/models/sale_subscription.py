# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models
from datetime import date


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"
    is_active = fields.Boolean(string="Active", default=True)
    initial_sale_order_id = fields.Many2one("sale.order", string="Initial Sale Order")
    # !!!
    # is_co_op = fields.Boolean(related="initial_sale_order_id.is_ratio", string="Co-op")
    # co_op_percentage = fields.Float(string="Co Op Percentage")
    active = fields.Boolean(string="Active", default=True)
    #co-op change!!!!
    co_opp_partner_ids = fields.One2many(
        related="initial_sale_order_id.co_op_sale_order_partner_ids", string="Co-Op Customers"
    )

    def deactivate_finished_subscriptins(self):
        today = date.today()
        subscriptions = self.env["sale.subscription"].search([("is_active", "=", True)], order="")
        for subscription in subscriptions:
            sub_lines = self.env["sale.subscription.line"].search(
                [("analytic_account_id", "=", subscription.id)], order=""
            )
            deactive_flag = len(list(filter(lambda x: (not x.end_date or x.end_date > today), sub_lines)))
            if not deactive_flag:
                subscription.is_active = False

    def partial_invoice_line(self, sale_order, option_line, refund=False, date_from=False):
        """Add an invoice line on the sales order for the specified option and add a discount
        to take the partial recurring period into account"""
        order_line_obj = self.env["sale.order.line"]
        ratio, message, period_msg = self._partial_recurring_invoice_ratio(date_from=date_from)
        if message != "":
            sale_order.message_post(body=message)
        _discount = (1 - ratio) * 100
        values = {
            "order_id": sale_order.id,
            "product_id": option_line.product_id.id,
            "subscription_id": self.id,
            "product_uom_qty": option_line.quantity,
            "product_uom": option_line.uom_id.id,
            "discount": _discount,
            "price_unit": option_line[0].price,
            "name": option_line.name,
        }
        return order_line_obj.create(values)

    def _get_product_from_line(self):
        """
        set product_id from the recurring invoice line field.
        """
        for subscription in self:
            product_id = subscription.recurring_invoice_line_ids.mapped("product_id")
            subscription.product_id = product_id[0].id if product_id else False

    def _get_description_from_line(self):
        for subscription in self:
            if subscription.recurring_invoice_line_ids:
                subscription.product_des = subscription.recurring_invoice_line_ids[0].name
            else:
                subscription.product_des = False

    product_id = fields.Many2one("product.product", string="Product", compute="_get_product_from_line")
    product_des = fields.Char(string="Description", compute="_get_description_from_line")

    def _compute_invoice_count(self):
        invoice = self.env["account.move"]
        can_read = invoice.check_access_rights("read", raise_exception=False)
        for subscription in self:
            subscription.invoice_count = (
                can_read
                and invoice.search_count(
                    [
                        "|",
                        ("invoice_line_ids.subscription_id", "=", subscription.id),
                        ("invoice_line_ids.subscription_ids", "in", subscription.id),
                    ]
                )
                or 0
            )

    def action_subscription_invoice(self):
        self.ensure_one()
        invoices = self.env["account.move"].search(
            [
                "|",
                ("invoice_line_ids.subscription_id", "in", self.ids),
                ("invoice_line_ids.subscription_ids", "in", self.id),
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


class SaleSubscriptionLine(models.Model):
    """
    Inherited to setup fields like.
        Start & End Date : Shows subscription life
        SO Lines: TO link SO line to manage amount
        Origin: It helps to identify that current line is Base/Upsell/Downsell
    """

    _inherit = "sale.subscription.line"

    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    so_line_id = fields.Many2one("sale.order.line", string="SO Lines")
    line_type = fields.Selection(
        [("base", "Base"), ("upsell", "Upsell"), ("downsell", "Downsell")], string="Origin", default="base"
    )
    active = fields.Boolean(string="Active", default=True)
