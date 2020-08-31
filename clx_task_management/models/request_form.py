# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, api, models, _


class RequestForm(models.Model):
    _name = 'request.form'
    _description = 'Request Form'

    name = fields.Char(string='Name')
    partner_id = fields.Many2one('res.partner', string='Customer')
    request_date = fields.Date('Date')
    description = fields.Text('Description', help="It will be set as project title")
    request_line = fields.One2many('request.form.line', 'request_form_id',
                                   string='Line Item Details')
    state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted')], string='state',
                             default='draft')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('request.form')
        return super(RequestForm, self).create(vals)

    def prepared_task_vals(self, line, project_id):
        """
        prepared dictionary for the create task
        :Param : line : browsable object of the item line
        :Param : project_id : browsable object of the project
        return : dictionary of the task
        """
        vals = {
            'name': line.description,
            'project_id': project_id.id
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
            'name': description
        }
        return vals

    def action_submit_form(self):
        self.ensure_one()
        project_id = False
        project_obj = self.env['project.project']
        project_task_obj = self.env['project.task']
        if self.description and self.partner_id:
            vals = self.prepared_project_vals(self.description, self.partner_id)
            if vals:
                project_id = project_obj.create(vals)
            for line in self.request_line:
                if project_id:
                    task_vals = self.prepared_task_vals(line, project_id)
                    project_task_obj.create(task_vals)
        self.state = 'submitted'


class RequestFormLine(models.Model):
    _name = 'request.form.line'
    _description = 'Request Form Line'
    _rec_name = 'request_form_id'

    request_form_id = fields.Many2one('request.form', string='Request Form', ondelete='cascade')
    req_type = fields.Selection([('new', 'New'), ('update', 'Update')], string='Request Type')
    task_id = fields.Many2one('main.task', string='Task')
    description = fields.Text(string='Description', help='It will set as Task Description')
