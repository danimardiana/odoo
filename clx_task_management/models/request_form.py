# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, api, models, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
import datetime
from pytz import timezone


class RequestForm(models.Model):
    _name = 'request.form'
    _description = 'Request Form'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Name', copy=False)
    partner_id = fields.Many2one('res.partner', string='Customer')
    request_date = fields.Datetime(
        'Request Submission Date', default=datetime.datetime.today(), copy=False)
    description = fields.Text('Project Title',
                              help="Choose a title for this client’s project request")
    request_line = fields.One2many('request.form.line', 'request_form_id',
                                   string='Line Item Details')
    state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted')],
                             string='state',
                             default='draft', tracking=True)
    is_create_client_launch = fields.Boolean(
        'Is this a brand new media campaign launch or relaunch?')
    ads_link_ids = fields.One2many(
        related='partner_id.ads_link_ids', string="Ads Link")
    intended_launch_date = fields.Date(string='Intended Launch Date')
    attachment_ids = fields.One2many(
        'request.form.attachments', 'req_form_id', string="Attachments")
    sale_order_id = fields.Many2many('sale.order', string="Sale Order")
    clx_attachment_ids = fields.Many2many(
        "ir.attachment", 'att_rel', 'attach_id', 'clx_id', string="Files", help="Upload multiple files here."
    )
    submitted_by_user_id = fields.Many2one("res.users", string="Submitted By")
    priority = fields.Selection(
        [('high', 'High'), ('regular', 'Regular')], default='regular', string="Priority")
    update_all_products = fields.Boolean(string="Update All Products")
    update_products_des = fields.Text(string="Update Products Description")
    project_id = fields.Many2one('project.project', string="Project")
    product_ids = fields.Many2many('product.product', string="Products")

    def open_active_subscription_line(self):
        """
        this method is used for open Active sale order of the particular customer from the request form.
        :return: action of sale order
        """
        action = self.env.ref(
            'clx_task_management.action_sale_subscription_line').read()[0]
        today = fields.Date.today()
        subscriptions = self.env['sale.subscription'].search(
            [('partner_id', '=', self.partner_id.id)])
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
            client_launch_task = self.env.ref(
                'clx_task_management.clx_client_launch_task')
            if client_launch_task:
                vals = {
                    'name': client_launch_task.name,
                    'project_id': project_id.id,
                    'stage_id': stage_id.id,
                    'repositary_task_id': client_launch_task.id,
                    'req_type': client_launch_task.req_type,
                    'team_ids': client_launch_task.team_ids.ids,
                    'team_members_ids': client_launch_task.team_members_ids.ids,
                    'tag_ids': client_launch_task.tag_ids.ids if client_launch_task.tag_ids else False
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
                            'team_ids': sub_task.team_ids.ids,
                            'team_members_ids': sub_task.team_members_ids.ids,
                            'parent_id': main_task.id,
                            'sub_task_id': sub_task.id,
                            'tag_ids': sub_task.tag_ids.ids if sub_task.tag_ids else False
                        }
                        project_task_obj.create(sub_task_vals)

    def assign_stage_project(self, project_id):
        """
        assign demo data stage to new created project
        :param project_id:
        :return:
        """
        stages = self.env['project.task.type'].search(
            [('demo_data', '=', True)])
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
        :param main_task: browsable object of the project.task
        :param line: browsable object of the request.line
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
                'team_ids': sub_task.team_ids.ids,
                'team_members_ids': sub_task.team_members_ids.ids,
                'date_deadline': main_task.date_deadline,
                'tag_ids': sub_task.tag_ids.ids if sub_task.tag_ids else False,
                'account_user_id': main_task.project_id.partner_id.account_user_id.id if main_task.project_id.partner_id.account_user_id else False,
                'clx_priority': main_task.project_id.priority,
                'description': line.description,
                'clx_attachment_ids': self.clx_attachment_ids.ids,
                'category_id': line.category_id.id if line.category_id else False
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

        current_date = self.calculated_date(line)

        vals = {
            'name': line.task_id.name,
            'project_id': project_id.id,
            'description': line.description.replace('\n', '<br/>'),
            'stage_id': stage_id.id,
            'repositary_task_id': line.task_id.id,
            'req_type': line.task_id.req_type,
            'team_ids': line.task_id.team_ids.ids,
            'team_members_ids': line.task_id.team_members_ids.ids,
            'date_deadline': self.intended_launch_date if self.intended_launch_date else current_date,
            'requirements': line.requirements,
            'tag_ids': line.task_id.tag_ids.ids if line.task_id.tag_ids else False,
            'account_user_id': project_id.partner_id.account_user_id.id if project_id.partner_id.account_user_id else False,
            'clx_priority': self.priority,
            'clx_attachment_ids': self.clx_attachment_ids.ids,
            'category_id': line.category_id.id if line.category_id else False
        }
        return vals

    def prepared_project_vals(self, description, partner_id):
        """
        prepared dictionary for the create project
        :Param : description : Title of the project
        :Param : partner_id : browsable object of the partner
        :return : return dictionary
        """
        max_date = max(map(self.calculated_date, self.request_line))

        vals = {
            'partner_id': partner_id.id,
            'name': description,
            'clx_state': 'new',
            'clx_sale_order_ids': self.sale_order_id.ids if self.sale_order_id.ids else False,
            'user_id': self.partner_id.account_user_id.id if self.partner_id.account_user_id else False,
            'deadline': max_date,
            'priority': self.priority,
            'clx_attachment_ids': self.clx_attachment_ids.ids
        }
        return vals

    def _send_request_form_mail(self):
        web_base_url = self.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        action_id = self.env.ref(
            'project.open_view_project_all', raise_if_not_found=False)
        link = """{}/web#id={}&view_type=form&model=project.project&action={}""".format(web_base_url,
                                                                                        self.project_id.id,
                                                                                        action_id.id)
        context = self._context.copy() or {}
        context.update({'link': link})
        email_template = self.env.ref(
            'clx_task_management.mail_template_request_form', raise_if_not_found=False)
        if email_template:
            email_template.with_context(context).send_mail(
                self.id, force_send=True)

    @api.onchange('priority')
    def _onchange_priority(self):
        for line in self.request_line:
            if hasattr(line, 'req_type'):
                today = fields.Date.today() if fields.Date.today() else datetime.datetime.today()
                current_day_with_time = self.write_date if self.write_date else datetime.datetime.today()
                user_tz = line.env.user.tz or 'US/Pacific'
                current_day_with_time = timezone('UTC').localize(
                    current_day_with_time).astimezone(timezone(user_tz))
                date_time_str = today.strftime("%d/%m/%y")
                date_time_str += ' 14:00:00'
                comparsion_date = datetime.datetime.strptime(
                    date_time_str, '%d/%m/%y %H:%M:%S')
                # if current_day_with_time after 2 pm:
                #     today + 1 day
                business_days_to_add = 0
                if current_day_with_time.time() > comparsion_date.time() or today.weekday() > 4:
                    business_days_to_add += 1

                if line.request_form_id.priority != 'high':
                    business_days_to_add += 2

                if line.req_type in ('update', 'budget'):
                    business_days_to_add += 0
                else:
                    business_days_to_add += 2

                current_date = today
                # code for skip saturday and sunday for set deadline on task.
                while business_days_to_add > 0:
                    current_date += datetime.timedelta(days=1)
                    weekday = current_date.weekday()
                    if weekday >= 5:  # sunday = 6, saturday = 5
                        continue
                    business_days_to_add -= 1

                line.task_deadline = current_date

    def calculated_date(self, line):
        today = fields.Date.today()
        current_day_with_time = self.write_date
        user_tz = self.env.user.tz or 'US/Pacific'
        current_day_with_time = timezone('UTC').localize(
            current_day_with_time).astimezone(timezone(user_tz))
        date_time_str = today.strftime("%d/%m/%y")
        date_time_str += ' 14:00:00'
        comparsion_date = datetime.datetime.strptime(
            date_time_str, '%d/%m/%y %H:%M:%S')
        # if current_day_with_time after 2 pm:
        #     today + 1 day
        business_days_to_add = 0
        if current_day_with_time.time() > comparsion_date.time() or today.weekday() > 4:
            business_days_to_add += 1

        if line.request_form_id.priority != 'high':
            business_days_to_add += 2

        if line.req_type in ('update', 'budget'):
            business_days_to_add += 0
        else:
            business_days_to_add += 2

        current_date = today
        # code for skip saturday and sunday for set deadline on task.
        while business_days_to_add > 0:
            current_date += datetime.timedelta(days=1)
            weekday = current_date.weekday()
            if weekday >= 5:  # sunday = 6, saturday = 5
                continue
            business_days_to_add -= 1

        return current_date

    def action_submit_form(self):
        """
        when request form is submitted create project and task and subtask from the Master table.
        :return:
        """
        self.ensure_one()
        if self.request_line and self.intended_launch_date:
            max_date = max(map(self.calculated_date, self.request_line))
            if self.intended_launch_date < max_date:
                raise UserError('Please check Intended launch Date !!')
        project_id = False
        project_obj = self.env['project.project']
        project_task_obj = self.env['project.task']
        sub_task_obj = self.env['sub.task']
        cl_task = self.env.ref(
            'clx_task_management.clx_client_launch_sub_task_1', raise_if_not_found=False)
        if not self.description:
            raise UserError('Please add Project Title!!')
        if not self.request_line:
            raise UserError('There is no Request Line, Please add some line')
        if self.request_line and any(not line.description or not line.task_id for line in self.request_line):
            raise UserError(
                'Please add some Instruction on every line If do not have description Please delete that line.')

        subscriptions = self.env['sale.subscription'].search(
            [('partner_id', '=', self.partner_id.id)])
        if not subscriptions:
            raise UserError(
                'You can not submit request form there is no active sale for this customer!!')
        if self.description and self.partner_id:
            vals = self.prepared_project_vals(self.description,
                                              self.partner_id)
            if vals:
                project_id = project_obj.create(vals)
                if project_id:
                    project_id.req_form_id = self.id
                    self.project_id = project_id.id
                    self.assign_stage_project(project_id)
                    # if self.is_create_client_launch:
                    #     self.create_client_launch_task(project_id)
                    for line in self.request_line:
                        if line.task_id:
                            vals = self.prepared_task_vals(line, project_id)
                            main_task = project_task_obj.create(vals)
                            if main_task:
                                dependency_sub_tasks = sub_task_obj. \
                                    search(
                                        [('parent_id', '=', line.task_id.id),
                                         '|', ('dependency_ids', '=', False),
                                         ('dependency_ids', '=', cl_task and cl_task.id)])
                                for sub_task in dependency_sub_tasks:
                                    vals = self.prepared_sub_task_vals(
                                        sub_task, main_task, line)
                                    project_task_obj.create(vals)
        self.state = 'submitted'
        self.submitted_by_user_id = self.env.uid
        self._send_request_form_mail()

    @api.onchange('partner_id', 'is_create_client_launch')
    def _onchange_partner_id(self):
        list_product = []
        req_line_obj = self.env['request.form.line']
        main_task_obj = self.env['main.task']
        if not self.is_create_client_launch:
            client_launch_task = self.env.ref(
                'clx_task_management.clx_client_launch_task', raise_if_not_found=False)
            available_line = self.request_line.filtered(
                lambda x: client_launch_task and x.task_id.id == client_launch_task.id)
            if available_line:
                available_line.unlink()
        else:
            client_launch_task = self.env.ref(
                'clx_task_management.clx_client_launch_task')
            auto_tasks = self.env.user.company_id.auto_add_main_task_ids if self.env.user.company_id and self.env.user.company_id.auto_add_main_task_ids else False
            for a_task in auto_tasks:
                vals = {
                    'req_type': a_task.req_type,
                    'task_id': a_task.id,
                    'requirements': a_task.requirements,
                    'description': a_task.requirements
                }
                form_line_id = req_line_obj.create(vals)
                list_product.append(form_line_id.id)
        today = fields.Date.today()
        lines = self.env['sale.order.line'].search(
            [('order_partner_id', '=', self.partner_id.id)])
        order_lines = False
        if lines:
            order_lines = lines
            order_lines = order_lines.filtered(
                lambda x: x.subscription_id.is_active and x.product_id.is_task_create)
            for category in order_lines.mapped('product_id').mapped('categ_id'):
                # task_id = main_task_obj.search([('product_ids', 'in', product.id), ('req_type', '=', 'update')])
                line_id = req_line_obj.create({
                    'category_id': category.id,
                    'req_type': 'update',
                    # 'task_id': task_id[0].id if task_id else False
                })
                list_product.append(line_id.id)
        self.update({'request_line': [(6, 0, list_product)],
                     'product_ids': order_lines.mapped('product_id') if order_lines else False})

    def update_description(self):
        for line in self.request_line:
            if self.update_products_des and self.update_all_products:
                if line.description and self.update_products_des not in line.description:
                    line.description += "\n \n" + self.update_products_des
                else:
                    line.description = self.update_products_des
                line.req_type = 'update'


class RequestFormLine(models.Model):
    _name = 'request.form.line'
    _description = 'Request Form Line'
    _rec_name = 'request_form_id'

    request_form_id = fields.Many2one('request.form', string='Request Form',
                                      ondelete='cascade')
    req_type = fields.Selection([('new', 'New'), ('update', 'Update'), ('budget', 'Budget')],
                                string='Request Type')
    task_id = fields.Many2one('main.task', string='Task')
    task_deadline = fields.Date(
        string='Deadline', readonly=True, copy=False, compute='_default_task_deadline')
    description = fields.Text(string='Instruction',
                              help='It will set as Task Description')
    requirements = fields.Text(string='Requirements')
    category_id = fields.Many2one(
        'product.category', string="Products Category")

    def create_task_deadline_date(self):
        today = fields.Date.today()
        current_day_with_time = self.write_date or datetime.datetime.utcnow()
        user_tz = self.env.user.tz or 'US/Pacific'
        current_day_with_time = timezone('UTC').localize(current_day_with_time).astimezone(timezone(user_tz))
        date_time_str = today.strftime("%d/%m/%y")
        date_time_str += ' 14:00:00'
        comparsion_date = datetime.datetime.strptime(
            date_time_str, '%d/%m/%y %H:%M:%S')
        # if current_day_with_time after 2 pm:
        #     today + 1 day
        business_days_to_add = 0
        if current_day_with_time.time() > comparsion_date.time() or today.weekday() > 4:
            business_days_to_add += 1

        if self.request_form_id.priority != 'high':
            business_days_to_add += 2

        if self.req_type in ('update', 'budget'):
            business_days_to_add += 0
        else:
            business_days_to_add += 2

        current_date = today
        # code for skip saturday and sunday for set deadline on task.
        while business_days_to_add > 0:
            current_date += datetime.timedelta(days=1)
            weekday = current_date.weekday()
            if weekday >= 5:  # sunday = 6, saturday = 5
                continue
            business_days_to_add -= 1

        self.task_deadline = current_date

    def _default_task_deadline(self):
        for line in self:
            line.create_task_deadline_date()

    @api.onchange('req_type')
    def _onchange_req_type(self):
        self.create_task_deadline_date()

    @api.onchange('task_id')
    def _onchange_task_id(self):
        if self.task_id:
            self.requirements = self.task_id.requirements
            self.description = self.task_id.requirements

    @api.onchange('req_type')
    def _onchange_main_task(self):
        if self.req_type and self.req_type == 'update':
            subscriptions = self.env['sale.subscription'].search(
                [('partner_id', '=', self.request_form_id.partner_id.id)])
            if not subscriptions:
                raise UserError(_(
                    """There is no subscription available for this customer."""))
        if not self.category_id:
            return {'domain': {'task_id': [('req_type', '=', self.req_type),
                                           ('pull_to_request_form', '=', True)]}}
        elif self.category_id:
            return {'domain': {'task_id': [('req_type', '=', self.req_type),
                                           ('category_id', '=',
                                            self.category_id.id),
                                           ('pull_to_request_form', '=', True)]}}
