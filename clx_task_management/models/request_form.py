# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, api, models, _
from odoo.exceptions import UserError
import datetime


class RequestForm(models.Model):
    _name = 'request.form'
    _description = 'Request Form'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', copy=False)
    partner_id = fields.Many2one('res.partner', string='Customer')
    request_date = fields.Datetime('Launch Date', default=fields.Date.today())
    description = fields.Text('Project Title',
                              help="Choose a title for this client’s project request")
    request_line = fields.One2many('request.form.line', 'request_form_id',
                                   string='Line Item Details')
    state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted')],
                             string='state',
                             default='draft', tracking=True)
    is_create_client_launch = fields.Boolean('Is this a brand new client launch?')
    ads_link_ids = fields.One2many(related='partner_id.ads_link_ids', string="Ads Link")
    intended_launch_date = fields.Date(string='Intended Launch Date')
    attachment_ids = fields.One2many('request.form.attachments', 'req_form_id', string="Attachments")

    def open_active_subscription_line(self):
        """
        this method is used for open Active sale order of the particular customer from the request form.
        :return: action of sale order
        """
        action = self.env.ref('clx_task_management.action_sale_subscription_line').read()[0]
        today = fields.Date.today()
        subscriptions = self.env['sale.subscription'].search([('partner_id', '=', self.partner_id.id)])
        if not subscriptions:
            raise UserError(_("No active Subscription for customer"))
        active_subscription_lines = subscriptions.recurring_invoice_line_ids.filtered(
            lambda x: x.start_date and x.start_date <= today and not x.end_date)
        if not active_subscription_lines:
            raise UserError(_("No active Subscription for customer"))
        action['domain'] = [('id', 'in', active_subscription_lines.ids)]
        return action

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('request.form')
        return super(RequestForm, self).create(vals)

    def unlink(self):
        for req_form in self:
            if req_form.state == 'submitted':
                raise UserError(_('You can Not Delete Submitted Request Form'))
        return super(RequestForm, self).unlink()

    def create_client_launch_task(self, project_id):
        """
        Create Client launch task is the is_create_client_launch is checked.
        :return:
        """
        project_task_obj = self.env['project.task']
        stage_id = self.env.ref('clx_task_management.clx_project_stage_1')
        if project_id:
            client_launch_task = self.env.ref('clx_task_management.clx_client_launch_task')
            if client_launch_task:
                vals = {
                    'name': client_launch_task.name,
                    'project_id': project_id.id,
                    'stage_id': stage_id.id,
                    'repositary_task_id': client_launch_task.id,
                    'req_type': client_launch_task.req_type,
                    'team_id': client_launch_task.team_id.id,
                    'team_members_ids': client_launch_task.team_members_ids.ids
                }
                main_task = project_task_obj.create(vals)
                sub_tasks = self.env['sub.task'].search([('parent_id', '=', client_launch_task.id),
                                                         ('dependency_ids', '=', False)])
                if sub_tasks:
                    for sub_task in sub_tasks:
                        sub_task_vals = {

                            'name': sub_task.sub_task_name,
                            'project_id': project_id.id,
                            'stage_id': stage_id.id,
                            'sub_repositary_task_ids': sub_task.dependency_ids.ids,
                            'team_id': sub_task.team_id.id,
                            'team_members_ids': sub_task.team_members_ids.ids,
                            'parent_id': main_task.id,
                            'sub_task_id': sub_task.id
                        }
                        project_task_obj.create(sub_task_vals)

    def assign_stage_project(self, project_id):
        """
        assign demo data stage to new created project
        :param project_id:
        :return:
        """
        stages = self.env['project.task.type'].search([('demo_data', '=', True)])
        for stage in stages:
            project_list = stage.project_ids.ids
            project_list.append(project_id.id)
            stage.update({'project_ids': [(6, 0, project_list)]})

    def open_project_main_task_kanban_view(self):
        """
        open project's main task kanban view
        :return: action of kanban view

        """
        project_action = self.env.ref('project.action_view_task')
        project = self.env['project.project'].search(
            [('req_form_id', '=', self.id)], limit=1)
        if project_action and project:
            action = project_action.read()[0]
            action["context"] = {'search_default_project_id': project.id}
            action["domain"] = [('parent_id', '=', False)]
            return action
        return False

    def prepared_sub_task_vals(self, sub_task, main_task, line):
        """
        Prepared vals for sub task
        :param sub_task: browsable object of the sub.task
        :param main_task: brwosable object of the main.task
        :param line: brwosable object of the request.line
        :return: dictionary for the sub task
        """
        stage_id = self.env.ref('clx_task_management.clx_project_stage_1')
        today = fields.Date.today()
        if line.req_type == 'update':
            business_days_to_add = 3
        else:
            business_days_to_add = 5
        current_date = today
        # code for skip saturday and sunday for set deadline on task.
        while business_days_to_add > 0:
            current_date += datetime.timedelta(days=1)
            weekday = current_date.weekday()
            if weekday >= 5:  # sunday = 6, saturday = 5
                continue
            business_days_to_add -= 1
        if stage_id:
            vals = {
                'name': sub_task.sub_task_name,
                'project_id': main_task.project_id.id,
                'stage_id': stage_id.id,
                'sub_repositary_task_ids': sub_task.dependency_ids.ids,
                'parent_id': main_task.id,
                'sub_task_id': sub_task.id,
                'team_id': sub_task.team_id.id,
                'team_members_ids': sub_task.team_members_ids.ids,
                'date_deadline': current_date
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
            'req_type': line.task_id.req_type,
            'team_id': line.task_id.team_id.id,
            'team_members_ids': line.task_id.team_members_ids.ids,
            'date_deadline': self.request_date if self.request_date else False,
            'requirements': line.requirements
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
        """
        when request form is submitted create project and task and subtask from the Master table.
        :return:
        """
        self.ensure_one()
        project_id = False
        project_obj = self.env['project.project']
        project_task_obj = self.env['project.task']
        sub_task_obj = self.env['sub.task']
        cl_task = self.env.ref('clx_task_management.clx_client_launch_sub_task_1')
        if not self.request_line:
            raise UserError('There is no Request Line, Please add some line')
        today = fields.Date.today()
        subscriptions = self.env['sale.subscription'].search([('partner_id', '=', self.partner_id.id)])
        if not subscriptions:
            raise UserError('You can not submit request form there is no active sale for this customer!!')
        elif subscriptions:
            active_subscription_lines = subscriptions.recurring_invoice_line_ids.filtered(
                lambda x: x.start_date and x.start_date <= today and not x.end_date)
            if not active_subscription_lines:
                raise UserError('You can not submit request form there is no active sale for this customer!!')

        if self.description and self.partner_id:
            vals = self.prepared_project_vals(self.description,
                                              self.partner_id)
            if vals:
                project_id = project_obj.create(vals)
                if project_id:
                    project_id.req_form_id = self.id
                    self.assign_stage_project(project_id)
                    if self.is_create_client_launch:
                        self.create_client_launch_task(project_id)
                    for line in self.request_line:
                        if line.task_id:
                            vals = self.prepared_task_vals(line, project_id)
                            main_task = project_task_obj.create(vals)
                            if main_task:
                                dependency_sub_tasks = sub_task_obj. \
                                    search(
                                    [('parent_id', '=', line.task_id.id),
                                     '|', ('dependency_ids', '=', False), ('dependency_ids', '=', cl_task.id)])
                                for sub_task in dependency_sub_tasks:
                                    vals = self.prepared_sub_task_vals(
                                        sub_task, main_task, line)
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
    description = fields.Text(string='Instruction',
                              help='It will set as Task Description')
    sale_order_id = fields.Many2one('sale.order', string="Sale Order")
    requirements = fields.Text(string='Requirements')

    @api.onchange('req_type')
    def _onchange_main_task(self):
        if self.req_type and self.req_type == 'update':
            today = fields.Date.today()
            subscriptions = self.env['sale.subscription'].search(
                [('partner_id', '=', self.request_form_id.partner_id.id)])
            if not subscriptions:
                raise UserError(_(
                    """You can only create new request as customer do not have active subscription."""))
            if subscriptions:
                active_subscription_lines = subscriptions.recurring_invoice_line_ids.filtered(
                    lambda x: (x.start_date and x.end_date and x.start_date <= today <= x.end_date)
                              or (x.start_date and not x.end_date and x.start_date <= today)
                )
                if not active_subscription_lines:
                    raise UserError(_(
                        """You can only create new request as customer do not have active subscription."""))
                if active_subscription_lines:
                    sale_orders = active_subscription_lines.mapped('so_line_id').mapped('order_id')
                    if not sale_orders:
                        raise UserError(_(
                            """You can only create new request as customer do not have active subscription."""))
        client_launch_task = self.env.ref('clx_task_management.clx_client_launch_task')
        if client_launch_task:
            for line in self:
                if line.request_form_id.is_create_client_launch:
                    client_launch_task.active = False
                else:
                    client_launch_task.active = True
