# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import models, fields


class TaskCancelWarningWizard(models.TransientModel):
    _name = 'task.cancel.warning.wizard'

    sub_task_ids = fields.Many2many('sub.task')

    def create_sub_task(self, task, project_id):
        """
        prepared vals for subtask
        :param task: recordset of the sub.task
        :param project_id: recordset of the project.project
        :return: dictionary of the sub task for the project.task
        """
        stage_id = self.env.ref('clx_task_management.clx_project_stage_1')
        sub_task = project_id.task_ids.filtered(lambda x: x.sub_task_id.parent_id.id == task.parent_id.id)
        if stage_id:
            vals = {
                'name': task.sub_task_name,
                'project_id': project_id.id,
                'stage_id': stage_id.id,
                'sub_repositary_task_ids': task.dependency_ids.ids,
                'parent_id': sub_task.mapped('parent_id')[0].id,
                'sub_task_id': task.id,
                'team_id': task.team_id.id if task.team_id else False,
                'team_members_ids': task.team_members_ids.ids if task.team_members_ids else False
            }
            return vals

    def create_dependent_task(self):
        """
        create dependent task when user click on yes button on the wizard form.
        :return:
        """
        project_id = self._context.get('project_id', False)
        task_id = self._context.get('current_task', False)
        project_id = self.env['project.project'].browse(project_id)
        sub_task_id = self.env['project.task'].browse(task_id)
        cancel_stage = self.env.ref('clx_task_management.clx_project_stage_9')
        sub_task_id.stage_id = cancel_stage.id
        sub_task_obj = self.env['sub.task']
        if sub_task_id:
            parent_task_main_task = project_id.task_ids.mapped('sub_task_id').mapped('parent_id')
            dependency_tasks = sub_task_obj.search(
                [('dependency_ids', 'in', sub_task_id.sub_task_id.ids),
                 ('parent_id', 'in', parent_task_main_task.ids)])
            for task in dependency_tasks:
                vals = self.create_sub_task(task, project_id)
                self.env['project.task'].create(vals)

    def cancel_dependent_task(self):
        """
        Cancel the task when user cancel the task from the cancel button on the task form view.
        :return:
        """
        project_id = self._context.get('project_id', False)
        sub_tasks = self.env['project.task'].search([('sub_task_id', 'in', self.sub_task_ids.ids),
                                                     ('project_id', '=', project_id)
                                                     ])
        cancel_stage = self.env.ref('clx_task_management.clx_project_stage_9')
        task_id = self._context.get('current_task', False)
        if task_id:
            task_id = self.env['project.task'].browse(task_id)
            if task_id:
                task_id.stage_id = cancel_stage.id


class SubTaskCreateWizard(models.TransientModel):
    _name = 'sub.task.create.wizard'
