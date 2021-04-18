# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, api, models, _


class MainTask(models.Model):
    _name = 'main.task'
    _description = 'Main Task'

    name = fields.Char(string='name')
    team_ids = fields.Many2many('clx.team', string='Team')
    team_members_ids = fields.Many2many('res.users', string='Team Members')
    display_to_customer = fields.Boolean(string='Display To Customer')
    sub_task_count = fields.Integer(string="", compute='_compute_sub_task_count')
    req_type = fields.Selection([('new', 'New'), ('update', 'Update'), ('budget', 'Budget')], string='Request Type')
    active = fields.Boolean(default=True)
    requirements = fields.Text(string="Requirements")
    category_id = fields.Many2one('product.category', string="Product Category")
    tag_ids = fields.Many2many('project.tags', string="Tags")
    product_ids = fields.Many2many('product.product', string="Products")
    pull_to_request_form = fields.Boolean(string='Pull to the Request Form', default=True)
   
    # Analyst selected Client Launch Date
    # intended_launch_date = fields.Date(related="project_id.partner_id.intended_launch_date", string='Intended Launch Date', store=True)

    # @api.onchange('team_ids')
    # def _onchange_team_ids(self):
    #     if self.team_ids:
    #         for record in self:
    #             if record.team_ids:
    #                 record.team_members_ids = record.team_ids.team_members_ids.ids

    def _compute_sub_task_count(self):
        sub_task_obj = self.env['sub.task']
        for main_task in self:
            main_task.sub_task_count = sub_task_obj.search_count(
                [('parent_id', '=', main_task.id)]) or 0

    def open_subtask(self):
        self.ensure_one()
        sub_tasks = self.env['sub.task'].search([
            ('parent_id', '=', self.id)
        ])
        action = self.env.ref(
            'clx_task_management.action_sub_task').read()[0]
        action["context"] = {"create": False}
        if len(sub_tasks) > 1:
            action['domain'] = [('id', 'in', sub_tasks.ids)]
        elif len(sub_tasks) == 1:
            form_view = [(self.env.ref('clx_task_management.form_view_sub_task').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = sub_tasks.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
