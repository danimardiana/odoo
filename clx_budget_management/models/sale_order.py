# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _send_mail_budget_changes(self):
        try:
            email_template = self.env.ref("clx_budget_management.mail_template_budget_email")
        except:
            email_template = False
        if email_template and self.env.user.company_id and self.env.user.company_id.team_ids:
            team_members_emails = self.env.user.company_id.team_ids.mapped('team_members_ids')
            team_members_emails = ','.join(team_members_emails.mapped('email'))
            email_values = {'email_to': team_members_emails}
            email_template.send_mail(self.partner_id.id, email_values=email_values, force_send=True)

    def _action_confirm(self):
        """
        inherited method for create budget line when confirm the sale order
        """
        if self.partner_id.company_type_rel != 'company':
            raise UserError(_("Please select customer Company to Confirm the sale order"))
        res = super(SaleOrder, self)._action_confirm()
        self.env['sale.subscription']._create_sale_budget(self)
        self.env['sale.budget.changes']._create_sale_budget_changes(self)
        self.with_context(se_order_id=self.id)._send_mail_budget_changes()
        return res

    def open_budget_line(self):
        budget_lines = self.env['sale.budget.line'].search([('sol_id.order_id', '=', self.id)])
        if budget_lines:
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
