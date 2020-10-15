# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, models, api, _
from odoo.osv import expression
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        if self._context.get('active_sale_order') and self._context.get('req_partner_id'):
            domain = expression.AND(
                [args or []])
            active_subscription_lines = False
            sale_orders = False
            today = fields.Date.today()
            subscriptions = self.env['sale.subscription'].search(
                [('partner_id', '=', self._context.get('req_partner_id'))])
            if subscriptions:
                active_subscription_lines = subscriptions.recurring_invoice_line_ids.filtered(
                    lambda x: (x.start_date and x.end_date and x.start_date <= today <= x.end_date)
                              or (x.start_date and not x.end_date and x.start_date <= today)
                )
                future_subscription_lines = subscriptions.recurring_invoice_line_ids.filtered(
                    lambda x: x.start_date and x.start_date >= today)
                if active_subscription_lines:
                    sale_orders = active_subscription_lines.mapped('so_line_id').mapped('order_id')
                if future_subscription_lines:
                    sale_orders += future_subscription_lines.mapped('so_line_id').mapped('order_id')
            if sale_orders:
                domain = expression.AND(
                    [args or [], [('id', 'in', sale_orders.ids)]])
            return super(SaleOrder, self.sudo())._name_search(name=name, args=domain, operator=operator, limit=limit,
                                                              name_get_uid=name_get_uid)

    def _action_confirm(self):
        result = super(SaleOrder, self)._action_confirm()
        won_stage_id = self.env.ref('crm.stage_lead4')
        if won_stage_id and self.opportunity_id and self.opportunity_id.stage_id.id != won_stage_id.id:
            raise UserError(_("You will need WON stage of opportunity {} to Confirm the Sale order.").format(self.opportunity_id.name))

        for line in self.order_line:
            if line.task_id and not line.task_id.clx_sale_order_id and not line.task_id.clx_sale_order_line_id:
                line.task_id.write(
                    {
                        'clx_sale_order_id': line.order_id.id,
                        'clx_sale_order_line_id': line.id
                    }
                )
            if line.project_id and not line.project_id.clx_sale_order_id:
                line.project_id.write({
                    'clx_sale_order_id': line.order_id.id
                })
        return result
