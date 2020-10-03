# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _action_confirm(self):
        """
        inherited method for create budget line when confirm the sale order
        """
        if self.partner_id.company_type_rel != 'company':
            raise UserError(_("You can not confirm the Sale order Because Customer type is not Company Management!!"))
        res = super(SaleOrder, self)._action_confirm()
        self.env['sale.subscription']._create_sale_budget(self)
        return res

    def open_budget_line(self):
        budget_lines = self.env['sale.budget.line'].search([('sol_id.order_id', '=', self.id)])
        if budget_lines:
            print()
            action = self.env.ref(
                'clx_budget_management.action_sale_budget_line').read()[0]
            action["context"] = {"create": False}
            if len(budget_lines) > 1:
                action['domain'] = [('id', 'in', budget_lines.ids)]
            elif len(budget_lines) == 1:
                form_view = [(self.env.ref('clx_budget_management.sale_budget_line_form_view').id, 'form')]
                if 'views' in action:
                    action['views'] = form_view + [
                        (state, view)
                        for state, view in action['views'] if view != 'form']
                else:
                    action['views'] = form_view
                action['res_id'] = budget_lines.ids[0]
            else:
                action = {'type': 'ir.actions.act_window_close'}
            return action
