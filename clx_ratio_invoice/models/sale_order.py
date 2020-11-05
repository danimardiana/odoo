# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_ratio = fields.Boolean('Co - Op')
    co_op_sale_order_partner_ids = fields.One2many('co.op.sale.order.partner', 'sale_order_id', string="Co op Customer")

    def action_co_op_create_invoices(self):
        if self.is_ratio:
            co_op_partner = self.co_op_sale_order_partner_ids.mapped('partner_id')
            subscriptions = self.order_line.mapped('clx_subscription_ids')
            lines = subscriptions.recurring_invoice_line_ids
            areas_lines = lines.filtered(
                lambda sl: (sl.so_line_id.order_id.clx_invoice_policy_id.policy_type == 'arrears'))
            if areas_lines:
                for partner in co_op_partner:
                    partner_wise_lines = areas_lines.filtered(
                        lambda x: x.analytic_account_id.partner_id.id == partner.id)
                    partner.with_context(co_op_invoice_partner=partner.id).generate_arrears_invoice(partner_wise_lines)
            advance_lines = lines.filtered(
                lambda sl: (sl.so_line_id.order_id.clx_invoice_policy_id.policy_type == 'advance'))
            if advance_lines:
                for partner in co_op_partner:
                    partner_wise_lines = advance_lines.filtered(
                        lambda x: x.analytic_account_id.partner_id.id == partner.id)
                    partner.with_context(co_op_invoice_partner=partner.id).generate_advance_invoice(partner_wise_lines)

    @api.onchange('co_op_sale_order_partner_ids')
    def onchange_co_op_sale_order_partner_ids(self):
        ratio = 0
        for line in self.co_op_sale_order_partner_ids:
            ratio += line.ratio
        if ratio > 100:
            raise UserError(_("You Can not add more than 100% !!"))

    @api.onchange('is_ratio')
    def onchange_is_ratio(self):
        co_op = self.env['co.op.sale.order.partner']
        if self.partner_id:
            vals = {
                'partner_id': self.partner_id.id
            }
            co_op_partner_id = co_op.create(vals)
            self.co_op_sale_order_partner_ids = [(6, 0, co_op_partner_id.ids)]

    def action_open_subscriptions(self):
        res = super(SaleOrder, self).action_open_subscriptions()
        if self.is_ratio:
            action = self.env.ref('sale_subscription.sale_subscription_action').read()[0]
            subscriptions = self.order_line.mapped('clx_subscription_ids')
            if len(subscriptions) > 1:
                action['domain'] = [('id', 'in', subscriptions.ids)]
            elif len(subscriptions) == 1:
                form_view = [(self.env.ref('sale_subscription.sale_subscription_view_form').id, 'form')]
                if 'views' in res:
                    action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
                else:
                    action['views'] = form_view
                action['res_id'] = subscriptions.ids[0]
            else:
                action = {'type': 'ir.actions.act_window_close'}
            return action
        return res

    def _compute_subscription_count(self):
        for order in self:
            if not order.is_ratio:
                sub_count = len(self.env['sale.order.line'].read_group(
                    [('order_id', '=', order.id), ('subscription_id', '!=', False)],
                    ['subscription_id'], ['subscription_id']))
                order.subscription_count = sub_count
            elif order.is_ratio:
                sub_count = len(order.order_line.mapped('clx_subscription_ids'))
                order.subscription_count = sub_count


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    clx_subscription_ids = fields.Many2many('sale.subscription', copy=False)
