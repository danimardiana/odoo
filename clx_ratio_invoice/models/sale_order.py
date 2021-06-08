# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_co_op_create_invoices(self):
        if self.is_ratio:
            if self.subscription_management in ("upsell", "downsell"):
                return
            so_lines = self.env["sale.subscription.line"].search(
                [
                    ("so_line_id.order_id", "=", self.id),
                ]
            )
            current_month_start_day = fields.Date.today()
            end_date = current_month_start_day.replace(day=1) + relativedelta(
                months=self.clx_invoice_policy_id.num_of_month + 1
            )
            end_date = end_date - relativedelta(days=1)
            lines = so_lines.filtered(lambda x: x.start_date and x.start_date < end_date)
            count = self.clx_invoice_policy_id.num_of_month + 1
            if fields.Date.today().day >= 23:
                count += 1

            # co-op change!!!!
            for co_op_partner in self.co_op_sale_order_partner_ids:
                for i in range(0, count):
                    if co_op_partner.partner_id.invoice_selection == "sol":
                        co_op_partner.partner_id.with_context(
                            sol=True, partner_id=co_op_partner.partner_id.id, percantage=co_op_partner.ratio, co_op=True
                        ).generate_advance_invoice_co_op(so_lines)
                    else:
                        print("create category wise invoice")
                    # so_lines = lines.filtered(
                    #     lambda x: (not x.end_date and x.invoice_start_date and x.invoice_start_date < end_date)
                    #               or
                    #               (x.end_date and x.invoice_start_date and x.invoice_start_date < end_date)
                    # )

    # def action_open_subscriptions(self):
    #     res = super(SaleOrder, self).action_open_subscriptions()
    #     if self.is_ratio:
    #         action = self.env.ref('sale_subscription.sale_subscription_action').read()[0]
    #         subscriptions = self.order_line.mapped('clx_subscription_ids')
    #         if len(subscriptions) > 1:
    #             action['domain'] = [('id', 'in', subscriptions.ids)]
    #         elif len(subscriptions) == 1:
    #             form_view = [(self.env.ref('sale_subscription.sale_subscription_view_form').id, 'form')]
    #             if 'views' in res:
    #                 action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
    #             else:
    #                 action['views'] = form_view
    #             action['res_id'] = subscriptions.ids[0]
    #         else:
    #             action = {'type': 'ir.actions.act_window_close'}
    #         return action
    #     return res

    # def _compute_subscription_count(self):
    #     for order in self:
    #         if not order.is_ratio:
    #             sub_count = len(self.env['sale.order.line'].read_group(
    #                 [('order_id', '=', order.id), ('subscription_id', '!=', False)],
    #                 ['subscription_id'], ['subscription_id']))
    #             order.subscription_count = sub_count
    #         elif order.is_ratio:
    #             sub_count = len(order.order_line.mapped('clx_subscription_ids'))
    #             order.subscription_count = sub_count


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    co_op_sale_order_line_partner_ids = fields.One2many(
        "co.op.sale.order.partner", "sale_order_line_id", string="Co op Customer"
    )

    clx_subscription_ids = fields.Many2many("sale.subscription", copy=False)

    @api.onchange("co_op_sale_order_line_partner_ids")
    def onchange_co_op_sale_order_partner_ids(self):
        ratio = 0
        for line in self.co_op_sale_order_line_partner_ids:
            ratio += line.ratio
        if ratio > 100:
            raise UserError(_("You Can not add more than 100% !!"))

    # @api.onchange('is_ratio')
    # def onchange_is_ratio(self):
    #     co_op = self.env['co.op.sale.order.partner']
    #     if self.partner_id:
    #         vals = {
    #             'partner_id': self.partner_id.id
    #         }
    #         co_op_partner_id = co_op.create(vals)
    #         self.co_op_sale_order_partner_ids = [(6, 0, co_op_partner_id.ids)]