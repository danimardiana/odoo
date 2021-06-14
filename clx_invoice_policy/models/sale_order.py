# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError
from odoo.tools import float_is_zero, float_compare
from dateutil.relativedelta import relativedelta
from datetime import date


class SaleOrder(models.Model):
    _inherit = "sale.order"

    clx_invoice_policy_id = fields.Many2one("clx.invoice.policy", string="Invoice Policy")
    vertical_order = fields.Selection(related="partner_id.vertical", store=True)
    management_company_id = fields.Many2one(related="partner_id.management_company_type_id", store=True)
    ownership_company_id = fields.Many2one(related="partner_id.ownership_company_type_id", store=True)

    def _action_confirm(self):
        """
        Create draft invoice when confirm the sale order.
        if sale order line start date is in current month.
        than create invoice current month.
        :return:
        """
        res = super(SaleOrder, self)._action_confirm()

        # TODO: replacing the SB's invoicing functions and check the period to invoice

        start_date = self.contract_start_date.replace(day=1)
        # co-op changed!!!!
        partner_ids = []
        for line in self.order_line:
            partner_ids += line.co_op_sale_order_line_partner_ids.mapped("partner_id")
        partner_ids += [self.partner_id]

        for partner in partner_ids:
            self.env["sale.subscription"].invoicing_invoice_policy_range(
                **{
                    "partner": partner,
                    "order_id": False if self.subscription_management in ("upsell", "downsell") else self.id,
                    "start_date": start_date,
                }
            )
        return res

        # generates invoices for client (by SB), can be removed
        if self.is_ratio:
            return res
        if self.subscription_management in ("upsell", "downsell"):
            return res
        so_lines = self.env["sale.subscription.line"].search(
            [
                ("so_line_id.order_id", "=", self.id),
            ]
        )

        lines = so_lines.filtered(lambda x: x.start_date and x.start_date < end_date)
        count = self.clx_invoice_policy_id.num_of_month + 1

        if lines:
            so_lines = lines.filtered(lambda x: x.invoice_start_date.month == current_month_start_day.month)
            for i in range(0, count):
                if self.partner_id.invoice_selection:
                    # replacing the SB's invoicing functions
                    if self.partner_id.invoice_selection == "sol":
                        self.partner_id.with_context(cofirm_sale=True, sol=True).generate_advance_invoice(so_lines)
                    else:
                        self.partner_id.with_context(cofirm_sale=True).generate_advance_invoice(so_lines)
                so_lines = lines.filtered(
                    lambda x: (not x.end_date and x.invoice_start_date and x.invoice_start_date < end_date)
                    or (x.end_date and x.invoice_start_date and x.invoice_start_date < end_date)
                )
        return res

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        super(SaleOrder, self).onchange_partner_id()
        self.payment_term_id = self.payment_term_id.id if self.payment_term_id.id else 1

        if self.partner_id:
            self.clx_invoice_policy_id = (
                self.partner_id.clx_invoice_policy_id.id if self.partner_id.clx_invoice_policy_id else False
            )
            self.user_id = self.partner_id.account_user_id.id if self.partner_id.account_user_id else False

    @api.model
    def create(self, vals):
        so = super(SaleOrder, self).create(vals)
        if so.partner_id and not vals.get("clx_invoice_policy_id"):
            so.clx_invoice_policy_id = so.partner_id.clx_invoice_policy_id.id
        return so

    def _create_invoices_wizard(self, grouped=False, final=False):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        if not self.env["account.move"].check_access_rights("create", False):
            try:
                self.check_access_rights("write")
                self.check_access_rule("write")
            except AccessError:
                return self.env["account.move"]

        precision = self.env["decimal.precision"].precision_get("Product Unit of Measure")

        # 1) Create invoices.
        invoice_vals_list = []
        for order in self:
            pending_section = None

            # Invoice values.
            invoice_vals = order._prepare_invoice()
            order_line = order.order_line
            # Invoice line values (keep only necessary sections).
            if self._context.get("invoice_section"):
                order_line = self.env["sale.order.line"]
                policy_month = order.clx_invoice_policy_id.num_of_month
                end_date = fields.Date.today().replace(day=1) + relativedelta(months=policy_month + 1, days=-1)
                for line in order.order_line:
                    if line.start_date and line.start_date < end_date:
                        order_line += line
            for line in order_line:
                if line.display_type == "line_section":
                    pending_section = line
                    continue
                if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    continue
                if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final):
                    if pending_section:
                        invoice_vals["invoice_line_ids"].append((0, 0, pending_section._prepare_invoice_line()))
                        pending_section = None
                    invoice_vals["invoice_line_ids"].append((0, 0, line._prepare_invoice_line()))

            if not invoice_vals["invoice_line_ids"]:
                raise UserError(
                    _(
                        "There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered."
                    )
                )

            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(
                _(
                    "There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered."
                )
            )

        moves = self.env["account.move"].sudo().with_context(default_type="out_invoice").create(invoice_vals_list)
        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        if final:
            moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
        for move in moves:
            move.message_post_with_view(
                "mail.message_origin_link",
                values={"self": move, "origin": move.line_ids.mapped("sale_line_ids.order_id")},
                subtype_id=self.env.ref("mail.mt_note").id,
            )
        return moves
