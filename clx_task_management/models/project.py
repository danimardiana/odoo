# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class projectTaskType(models.Model):
    _inherit = 'project.task.type'

    demo_data = fields.Boolean()


class ProjectProject(models.Model):
    _inherit = 'project.project'

    req_form_id = fields.Many2one('request.form', string='Request Form')
    clx_state = fields.Selection([('in_progress', 'In Progress'), ('done', 'Done')], string="State")
    clx_sale_order_id = fields.Many2one('sale.order', string='Sale order')

    def action_done_project(self):
        tasks = self.env['project.task'].search([('project_id', '=', self.id)])
        complete_stage = self.env.ref('clx_task_management.clx_project_stage_8')
        if all(task.stage_id.id == complete_stage.id for task in tasks):
            self.clx_state = 'done'
        else:
            raise UserError(_("Please Complete All the Task First!!"))


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
    clx_sale_order_id = fields.Many2one('sale.order', string='Sale order')
    clx_sale_order_line_id = fields.Many2one('sale.order.line', string="Sale order Item")

    def prepared_sub_task_vals(self, sub_task, main_task):
        """
        Prepared vals for sub task
        :param sub_task: browsable object of the sub.task
        :param main_task: brwosable object of the main.task
        :return: dictionary for the sub task
        """
        stage_id = self.env.ref('clx_task_management.clx_project_stage_1')
        if stage_id:
            vals = {
                'name': sub_task.sub_task_name,
                'project_id': main_task.project_id.id,
                'stage_id': stage_id.id,
                'sub_repositary_task_ids': sub_task.dependency_ids.ids,
                'parent_id': main_task.id,
                'sub_task_id': sub_task.id,
                'team_id': sub_task.team_id.id,
                'team_members_ids': sub_task.team_members_ids.ids
            }
            return vals

    @api.depends('stage_id', 'kanban_state')
    def _compute_kanban_state_label(self):
        """
        Override this method because of when subtask is completed than
        automatically complete parent task and if parent task is completed
        than project is automatically done.
        :return:
        """
        for task in self:
            if task.kanban_state == 'normal':
                task.kanban_state_label = task.legend_normal
            elif task.kanban_state == 'blocked':
                task.kanban_state_label = task.legend_blocked
            else:
                task.kanban_state_label = task.legend_done
            complete_stage = self.env.ref('clx_task_management.clx_project_stage_8')
            tasks = task.parent_id.child_ids
            if all(task.stage_id.id == complete_stage.id for task in tasks):
                task.parent_id.stage_id = complete_stage.id
                if all(task.stage_id.id == complete_stage.id for task in
                       task.project_id.task_ids.filtered(lambda x: not x.parent_id)):
                    task.project_id.clx_state = 'done'

    def action_view_clx_so(self):
        """
        open sale order from project task form view via smart button
        :return:
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "views": [[False, "form"]],
            "res_id": self.clx_sale_order_id.id,
            "context": {"create": False, "show_sale": True},
        }

    def unlink(self):
        completed_stage = self.env.ref('clx_task_management.clx_project_stage_8')
        for task in self:
            task.project_id.message_post(body=_("""
                Task Has been Deleted By %s
                Task Name : %s
            """) % (self.env.user.name, task.name))
            if task.stage_id.id != completed_stage.id:
                params = self.env['ir.config_parameter'].sudo()
                auto_create_sub_task = bool(params.get_param('auto_create_sub_task')) or False
                if auto_create_sub_task:
                    main_task = task.project_id.task_ids.mapped('sub_task_id').mapped('parent_id')
                    sub_tasks = self.env['sub.task'].search(
                        [('parent_id', 'in', main_task.ids), ('dependency_ids', 'in', task.sub_task_id.ids)])
                    for sub_task in sub_tasks:
                        vals = self.create_sub_task(sub_task, task.project_id)
                        self.create(vals)
        return super(ProjectTask, self).unlink()

    def create_sub_task(self, task, project_id):
        """
        prepared vals for subtask
        :param task: recordset of the sub.task
        :param project_id: recordset of the project.project
        :return: dictionary of the sub task for the project.task
        """
        stage_id = self.env.ref('clx_task_management.clx_project_stage_1')
        sub_task = self.project_id.task_ids.filtered(lambda x: x.sub_task_id.parent_id.id == task.parent_id.id)
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

    def write(self, vals):
        res = super(ProjectTask, self).write(vals)
        sub_task_obj = self.env['sub.task']
        if vals.get('req_type', False) and vals.get('repositary_task_id', False):
            repositary_main_task = self.env['main.task'].browse(vals.get('repositary_task_id'))
            if repositary_main_task:
                repo_sub_tasks = sub_task_obj.search([('parent_id', '=', repositary_main_task.id),
                                                      ('dependency_ids', '=', False)])
                for sub_task in repo_sub_tasks:
                    vals = self.prepared_sub_task_vals(
                        sub_task, self)
                    self.create(vals)

        stage_id = self.env['project.task.type'].browse(vals.get('stage_id'))
        complete_stage = self.env.ref('clx_task_management.clx_project_stage_8')
        cancel_stage = self.env.ref('clx_task_management.clx_project_stage_9')
        if vals.get('stage_id', False) and stage_id.id == complete_stage.id:
            if self.sub_task_id:
                parent_task_main_task = self.project_id.task_ids.mapped('sub_task_id').mapped('parent_id')
                dependency_tasks = sub_task_obj.search(
                    [('dependency_ids', 'in', self.sub_task_id.ids),
                     ('parent_id', 'in', parent_task_main_task.ids)])
                for task in dependency_tasks:
                    vals = self.create_sub_task(task, self.project_id)
                    if not self.project_id.task_ids.filtered(lambda x: x.sub_task_id.id == task.id):
                        self.create(vals)
        elif vals.get('stage_id', False) and stage_id.id == cancel_stage.id:
            params = self.env['ir.config_parameter'].sudo()
            auto_create_sub_task = bool(params.get_param('auto_create_sub_task')) or False
            if auto_create_sub_task:
                main_task = self.project_id.task_ids.mapped('sub_task_id').mapped('parent_id')
                sub_tasks = self.env['sub.task'].search(
                    [('parent_id', 'in', main_task.ids), ('dependency_ids', 'in', self.sub_task_id.ids)])
                for sub_task in sub_tasks:
                    vals = self.create_sub_task(sub_task, self.project_id)
                    self.create(vals)

        return res

    def action_view_cancel_task(self):
        main_task = self.project_id.task_ids.mapped('sub_task_id').mapped('parent_id')
        sub_tasks = self.env['sub.task'].search(
            [('parent_id', 'in', main_task.ids), ('dependency_ids', 'in', self.sub_task_id.ids)])
        context = dict(self._context) or {}
        context.update({
            'project_id': self.project_id.id,
            'default_sub_task_ids': sub_tasks.ids,
            'current_task': self.id
        })
        view_id = self.env.ref('clx_task_management.task_cancel_warning_wizard_form_view').id
        return {'type': 'ir.actions.act_window',
                'name': _('Cancel Task'),
                'res_model': 'task.cancel.warning.wizard',
                'target': 'new',
                'view_mode': 'form',
                'views': [[view_id, 'form']],
                'context': context
                }
