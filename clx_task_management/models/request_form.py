# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, api, models, _


class RequestForm(models.Model):
    _name = 'request.form'
    _description = 'Request Form'

    name = fields.Char(string='Name', copy=False)
    partner_id = fields.Many2one('res.partner', string='Customer')
    request_date = fields.Date('Date')
    description = fields.Text('Description',
                              help="It will be set as project title")
    request_line = fields.One2many('request.form.line', 'request_form_id',
                                   string='Line Item Details')
    state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted')],
                             string='state',
                             default='draft')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('request.form')
        return super(RequestForm, self).create(vals)

    def open_project(self):
        project_view = self.env.ref('project.edit_project')
        project = self.env['project.project'].search(
            [('req_form_id', '=', self.id)], limit=1)
        if project and project_view:
            return {
                'name': _('Project'),
                'res_id': project.id,
                'res_model': 'project.project',
                'type': 'ir.actions.act_window',
                'view_id': project_view.id,
                'views': [(project_view.id, 'form')],
                'view_mode': 'form',
            }
        return False

    def prepared_sub_task_vals(self, sub_task, main_task):
        stage_id = self.env.ref('clx_task_management.clx_project_stage_1')
        if stage_id:
            vals = {
                'name': sub_task.sub_task_name,
                'project_id': main_task.project_id.id,
                'stage_id': stage_id.id,
                'sub_repositary_task_ids': sub_task.dependency_ids.ids,
                'parent_id': main_task.id,
                'sub_task_id': sub_task.id
            }
            return vals

    def prepared_task_vals(self, line, project_id):
        """
        prepared dictionary for the create task
        :Param : line : browsable object of the item line
        :Param : project_id : browsable object of the project
        return : dictionary of the task
        """
        stage_id = self.env.ref('clx_task_management.clx_project_stage_1')
        vals = {
            'name': line.task_id.name,
            'project_id': project_id.id,
            'description': line.description,
            'stage_id': stage_id.id,
            'repositary_task_id': line.task_id.id,
            'req_type': line.task_id.req_type
        }
        return vals

    def prepared_project_vals(self, description, partner_id):
        """
        prepared dictionary for the create project
        :Param : description : Title of the project
        :Param : partner_id : browsable object of the partner
        :return : return dictionary
        """
        vals = {
            'partner_id': partner_id.id,
            'name': description,
            'clx_state': 'in_progress'
        }
        return vals

    def action_submit_form(self):
        self.ensure_one()
        project_id = False
        project_obj = self.env['project.project']
        project_task_obj = self.env['project.task']
        sub_task_obj = self.env['sub.task']
        if self.description and self.partner_id:
            vals = self.prepared_project_vals(self.description,
                                              self.partner_id)
            if vals:
                project_id = project_obj.create(vals)
                if project_id:
                    project_id.req_form_id = self.id
                    for line in self.request_line:
                        if line.task_id:
                            vals = self.prepared_task_vals(line, project_id)
                            main_task = project_task_obj.create(vals)
                            if main_task:
                                without_dependency_sub_tasks = sub_task_obj. \
                                    search(
                                    [('parent_id', '=', line.task_id.id),
                                     ('dependency_ids', '=', False)])
                                for sub_task in without_dependency_sub_tasks:
                                    vals = self.prepared_sub_task_vals(
                                        sub_task, main_task)
                                    project_task_obj.create(vals)

        self.state = 'submitted'


class RequestFormLine(models.Model):
    _name = 'request.form.line'
    _description = 'Request Form Line'
    _rec_name = 'request_form_id'

    request_form_id = fields.Many2one('request.form', string='Request Form',
                                      ondelete='cascade')
    req_type = fields.Selection([('new', 'New'), ('update', 'Update')],
                                string='Request Type')
    task_id = fields.Many2one('main.task', string='Task')
    description = fields.Text(string='Description',
                              help='It will set as Task Description')
