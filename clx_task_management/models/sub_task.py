# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, api, models, _


class SubTask(models.Model):
    _name = 'sub.task'
    _description = 'sub Task'
    _order = 'sequence'

    @api.onchange('parent_id')
    def _onchange_tag_ids(self):
        for record in self:
            if record.parent_id and record.parent_id.tag_ids:
                record.tag_ids = record.parent_id.tag_ids.ids

    name = fields.Char(string='Name')
    sub_task_name = fields.Char(string='Sub Task Name')
    team_ids = fields.Many2many('clx.team', string='Team')
    parent_id = fields.Many2one('main.task', string='Parent Task', ondelete='cascade')
    team_members_ids = fields.Many2many('res.users', string='Team Members')
    display_to_customer = fields.Boolean(string='Display To Customer')
    dependency_ids = fields.Many2many('sub.task', 'clx_sub_task_sub_task_rel', 'sub_task_id',
                                      'sub_id')
    sequence = fields.Integer()
    stage_id = fields.Many2one('project.task.type', string='Stage')
    task_id = fields.Many2one('project.task', string="Task")
    tag_ids = fields.Many2many('project.tags', string="Tags")

    def redirect_task(self):
        if self.task_id:
            view_id = self.env.ref('project.view_task_form2').id
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'project.task',
                'target': 'self',
                'res_id': self.task_id.id,
                'views': [[view_id, 'form']],
            }

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('sub.task')
        return super(SubTask, self).create(vals)

    @api.onchange('stage_id', 'team_members_ids')
    def onchange_stage_id(self):
        if self.task_id:
            self.task_id.stage_id = self.stage_id.id
            self.task_id.team_members_ids = self.team_members_ids.ids

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
