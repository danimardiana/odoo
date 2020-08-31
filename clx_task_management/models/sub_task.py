# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, api, models, _


class SubTask(models.Model):
    _name = 'sub.task'
    _description = 'sub Task'

    name = fields.Char(string='name')
    sub_task_name = fields.Char(string='Sub Task Name')
    team_id = fields.Many2one('clx.team', string='Team')
    parent_id = fields.Many2one('main.task', string='Parent Task')
    team_members_ids = fields.Many2many('res.users', string='Team Members')
    display_to_customer = fields.Char(string='Display To Customer')
    dependency_id = fields.Many2one('sub.task',string='Dependency')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('sub.task')
        return super(SubTask, self).create(vals)

    def open_parent_task(self):
        self.ensure_one()
        sub_tasks = self.env['main.task'].search([
            ('id', '=', self.parent_id.id)
        ])
        action = self.env.ref(
            'clx_task_management.action_main_task').read()[0]
        action["context"] = {"create": False}
        if len(sub_tasks) > 1:
            action['domain'] = [('id', 'in', sub_tasks.ids)]
        elif len(sub_tasks) == 1:
            form_view = [(self.env.ref('clx_task_management.form_view_main_task').id, 'form')]
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
