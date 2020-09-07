# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, api, models, _


class MainTask(models.Model):
    _name = 'main.task'
    _description = 'Main Task'

    name = fields.Char(string='name')
    team_id = fields.Many2one('clx.team', string='Team')
    team_members_ids = fields.Many2many('res.users', string='Team Members')
    display_to_customer = fields.Boolean(string='Display To Customer')
    sub_task_count = fields.Integer(string="", compute='_compute_sub_task_count')
    req_type = fields.Selection([('new', 'New'), ('update', 'Update')], string='Request Type')
    is_create_client_launch = fields.Boolean()

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
