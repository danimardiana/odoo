# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, models, _
from odoo.exceptions import UserError


class projectTaskType(models.Model):
    _inherit = 'project.task.type'

    demo_data = fields.Boolean()


class ProjectProject(models.Model):
    _inherit = 'project.project'

    req_form_id = fields.Many2one('request.form', string='Request Form')
    clx_state = fields.Selection([('in_progress', 'In Progress'), ('done', 'Done')], string="State")


class ProjectTask(models.Model):
    _inherit = 'project.task'

    repositary_task_id = fields.Many2one('main.task', string='Repository Task')
    sub_repositary_task_ids = fields.Many2many('sub.task',
                                               string='Repository Sub Task')
    req_type = fields.Selection([('new', 'New'), ('update', 'Update')],
                                string='Request Type')
    sub_task_id = fields.Many2one('sub.task', string="Sub Task from Master Table")
    team_id = fields.Many2one('clx.team', string='Team')
    team_members_ids = fields.Many2many('res.users', string="Team Members")

    def unlink(self):
        for task in self:
            raise UserError(_('You can Not Delete the Task {} please contact Administrator.').format(task.name))
        return super(ProjectTask, self).unlink()

    def create_sub_task(self, task, project_id):
        stage_id = self.env.ref('clx_task_management.clx_project_stage_1')
        if stage_id:
            vals = {
                'name': task.sub_task_name,
                'project_id': project_id.id,
                'stage_id': stage_id.id,
                'sub_repositary_task_ids': task.dependency_ids.ids,
                'parent_id': self.parent_id.id,
                'sub_task_id': task.id
            }
            return vals

    def write(self, vals):
        res = super(ProjectTask, self).write(vals)
        sub_task_obj = self.env['sub.task']
        stage_id = self.env['project.task.type'].browse(vals.get('stage_id'))
        complete_stage = self.env.ref('clx_task_management.clx_project_stage_8')
        if vals.get('stage_id', False) and stage_id.id == complete_stage.id:
            if self.sub_task_id:
                dependency_tasks = sub_task_obj.search([('dependency_ids', 'in', self.sub_task_id.ids)])
                for task in dependency_tasks:
                    vals = self.create_sub_task(task, self.project_id)
                    self.create(vals)
        return res
