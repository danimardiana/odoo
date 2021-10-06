# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, api, models, _
from odoo.exceptions import UserError, ValidationError, Warning
from dateutil.relativedelta import relativedelta
import datetime
import os
from pytz import timezone


class RequestForm(models.Model):
    _name = "request.form"
    _description = "Request Form"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(string="Name", copy=False)
    partner_id = fields.Many2one("res.partner", string="Customer")
    request_date = fields.Datetime("Request Submission Date", default=datetime.datetime.today(), copy=False)
    description = fields.Text("Project Title", help="Choose a title for this client’s project request")
    request_line = fields.One2many("request.form.line", "request_form_id", string="Line Item Details")
    state = fields.Selection(
        [("draft", "Draft"), ("submitted", "Submitted")], string="state", default="draft", tracking=True
    )

    is_create_client_launch = fields.Boolean("Is this a brand new media campaign launch or relaunch?")
    ads_link_ids = fields.One2many(related="partner_id.ads_link_ids", string="Ads Link")

    intended_launch_date = fields.Date(string="Intended Launch Date")
    # Caluculated date derived from the form's max task due date
    max_proof_deadline_date = fields.Date(string="Project Due Date")

    attachment_ids = fields.One2many("request.form.attachments", "req_form_id", string="Attachments")
    sale_order_id = fields.Many2many("sale.order", string="Sale Order")
    clx_attachment_ids = fields.Many2many(
        "ir.attachment", "att_rel", "attach_id", "clx_id", string="Files", help="Upload multiple files here."
    )
    submitted_by_user_id = fields.Many2one("res.users", string="Submitted By")
    priority = fields.Selection([("high", "High"), ("regular", "Regular")], default="regular", string="Priority")
    update_all_products = fields.Boolean(string="Update All Products")
    update_products_des = fields.Text(string="Update Products Description")
    project_id = fields.Many2one("project.project", string="Project")
    product_ids = fields.Many2many("product.product", string="Products")
    override_project_check = fields.Boolean(string="Override Project Check", default=False)
    # Client Cancellation Fields
    cancel_client = fields.Boolean(string="Client Cancellation")
    cancel_service_date = fields.Date(string="Last Day of Service")
    cancel_user_id = fields.Many2one("res.users", string="Account Manager")
    cancel_client_type = fields.Selection(
        [
            ("other", "Other"),
            ("greystar", "Greystar"),
            ("ave5", "Avenue 5"),
        ],
        string="Preferred Client Type",
    )
    cancel_vertical = fields.Selection(
        [
            ("res", "RES"),
            ("srl", "SRL"),
            ("local", "Local"),
            ("auto", "Auto"),
        ],
        string="Vertical",
    )
    cancel_reason = fields.Selection(
        [
            ("stabilized_asset", "Stabilized Asset"),
            ("perf_issue", "Performance Issue"),
            ("loss_of_mgmt", "Loss of Management"),
            ("owner_dissatisfiled", "Ownership Dissatisfiled"),
            ("mgmt_dissatisfiled", "Management Dissatisfiled"),
            ("comp_loss", "Lost to a Competitor"),
            ("budget_constraints", "Budget Constraints"),
            ("term_notice", "Notice of Termination"),
            ("clx_other", "Other (CLX Lost Contract)"),
            ("na", "N/A"),
        ],
        string="Cancellation Reason",
    )
    cancel_reason_detail = fields.Text(string="Cancellation Reason Detail")
    cancel_reports = fields.Selection(
        [
            ("delete_today", "Delete reporting today."),
            ("delete_weekly_today", "Delete weekly reports today. Delete monthly reports after final reports issue."),
            ("delete_after_final", "Delete reporting after final reports issue."),
        ],
        string="Cancel - Automated Reports",
    )
    cancel_billing = fields.Selection(
        [
            ("full_month", "Spend a full month's budget in the remaining month."),
            ("half_month", "Spend a 1/2 month's budget in the remaining prorated month."),
        ],
        string="Cancel - Final Billing",
    )

    def open_active_subscription_line(self):
        """
        this method is used for open Active sale order of the particular customer from the request form.
        :return: action of sale order
        """
        action = self.env.ref("clx_task_management.action_sale_subscription_line").read()[0]
        today = fields.Date.today()
        subscriptions = self.env["sale.subscription"].search([("partner_id", "=", self.partner_id.id)])
        if not subscriptions:
            raise UserError(_("No active Subscription for customer"))
        active_subscription_lines = subscriptions.recurring_invoice_line_ids.filtered(
            lambda x: x.start_date and x.start_date <= today and not x.end_date
        )
        if not active_subscription_lines:
            raise UserError(_("No active Subscription for customer"))
        action["domain"] = [("id", "in", active_subscription_lines.ids)]
        return action

    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New"):
            vals["name"] = self.env["ir.sequence"].next_by_code("request.form")
        return super(RequestForm, self).create(vals)

    def unlink(self):
        for req_form in self:
            if req_form.state == "submitted":
                raise UserError(_("You can Not Delete Submitted Request Form"))
        return super(RequestForm, self).unlink()

    def _computed_max_proof_date(self):
        self.max_proof_deadline_date = fields.Date.today()

    def assign_stage_project(self, project_id):
        """
        assign demo data stage to new created project
        :param project_id:
        :return:
        """
        stages = self.env["project.task.type"].search([("demo_data", "=", True)])
        for stage in stages:
            project_list = stage.project_ids.ids
            project_list.append(project_id.id)
            stage.update({"project_ids": [(6, 0, project_list)]})

    def open_project_main_task_kanban_view(self):
        """
        open project's main task kanban view
        :return: action of kanban view

        """
        project_action = self.env.ref("clx_task_management.action_view_parent_task")
        project = self.env["project.project"].search([("req_form_id", "=", self.id)], limit=1)
        if project_action and project:
            action = project_action.read()[0]
            action["context"] = {"search_default_project_id": project.id}
            action["domain"] = [("parent_id", "=", False)]
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
        stage_id = self.env.ref("clx_task_management.clx_project_stage_1")

        if stage_id:
            vals = {
                "name": sub_task.sub_task_name,
                "project_id": main_task.project_id.id,
                "stage_id": stage_id.id,
                "sub_repositary_task_ids": sub_task.dependency_ids.ids,
                "parent_id": main_task.id,
                "sub_task_id": sub_task.id,
                "team_ids": sub_task.team_ids.ids,
                "clx_task_manager_id": main_task.clx_task_manager_id.id if main_task.clx_task_manager_id else False,
                "team_members_ids": sub_task.team_members_ids.ids,
                "date_deadline": main_task.date_deadline,
                "task_intended_launch_date": self.intended_launch_date
                if self.intended_launch_date
                else main_task.date_deadline,
                "tag_ids": sub_task.tag_ids.ids if sub_task.tag_ids else False,
                "account_user_id": main_task.project_id.partner_id.account_user_id.id
                if main_task.project_id.partner_id.account_user_id
                else False,
                "clx_priority": main_task.project_id.priority,
                "description": line.description,
                "requirements": line.requirements,
                "cancel_client": self.cancel_client,
                "clx_attachment_ids": self.clx_attachment_ids.ids,
                "category_id": line.category_id.id if line.category_id else False,
            }
            # print(vals)
            return vals

    def prepared_task_vals(self, line, project_id):
        """
        prepared dictionary for the create task
        :Param : line : browsable object of the item line
        :Param : project_id : browsable object of the project
        return : dictionary of the task
        """
        stage_id = self.env.ref("clx_task_management.clx_project_stage_1")

        # Proof Due Date/Deadline
        proof_deadline_date = self.calculated_date(line)

        if self.cancel_client:
            # Set the requirements field in all Tasks with the informtion
            # collected from the Client Cancellation Questionaire
            cancel_client_type_vals = dict(self._fields["cancel_client_type"].selection)
            cancel_vertical_vals = dict(self._fields["cancel_vertical"].selection)
            cancel_reason_vals = dict(self._fields["cancel_reason"].selection)
            cancel_reports_vals = dict(self._fields["cancel_reports"].selection)
            cancel_billing_vals = dict(self._fields["cancel_billing"].selection)

            client_type = cancel_client_type_vals.get(self.cancel_client_type)
            client_vertical = cancel_vertical_vals.get(self.cancel_vertical)
            reason = cancel_reason_vals.get(self.cancel_reason)
            reports = cancel_reports_vals.get(self.cancel_reports)
            billing = cancel_billing_vals.get(self.cancel_billing)

            line.requirements = (
                line.requirements
                + os.linesep
                + os.linesep
                + "Service Cancellation Date:  "
                + self.cancel_service_date.strftime("%m/%d/%Y")
                + os.linesep
                + os.linesep
                + "Preferred Client Type:  "
                + client_type
                + os.linesep
                + os.linesep
                + "Verical:  "
                + client_vertical
                + os.linesep
                + os.linesep
                + "Cancellation Reason:  "
                + reason
                + os.linesep
                + os.linesep
                + "Cancellation Detail:  "
                + self.cancel_reason_detail
                + os.linesep
                + os.linesep
                + "Cancel - Automated Reports:  "
                + reports
                + os.linesep
                + os.linesep
                + "Cancel - Final Billing:  "
                + billing
            )

        vals = {
            "name": line.task_id.name,
            "project_id": project_id.id,
            "description": line.description.replace("\n", "<br/>"),
            "stage_id": stage_id.id,
            "repositary_task_id": line.task_id.id,
            "req_type": line.task_id.req_type,
            "team_ids": line.task_id.team_ids.ids,
            "clx_task_manager_id": project_id.clx_project_manager_id.id if project_id.clx_project_manager_id else False,
            "team_members_ids": line.task_id.team_members_ids.ids,
            "date_deadline": proof_deadline_date,
            "task_intended_launch_date": self.intended_launch_date
            if self.intended_launch_date
            else proof_deadline_date,
            "requirements": line.requirements,
            "cancel_client": self.cancel_client,
            "tag_ids": line.task_id.tag_ids.ids if line.task_id.tag_ids else False,
            "account_user_id": project_id.partner_id.account_user_id.id
            if project_id.partner_id.account_user_id
            else False,
            "clx_priority": self.priority,
            "clx_attachment_ids": self.clx_attachment_ids.ids,
            "category_id": line.category_id.id if line.category_id else False,
        }
        return vals

    def prepared_project_vals(self, description, partner_id, cs_member=False):
        """
        prepared dictionary for the create project
        :Param : description : Title of the project
        :Param : partner_id : browsable object of the partner
        :return : return dictionary
        """

        max_date = max(map(self.calculated_date, self.request_line))
        launch_date = (
            self.intended_launch_date
            if self.intended_launch_date and self.intended_launch_date > self.max_proof_deadline_date
            else self.max_proof_deadline_date
        )

        vals = {
            "partner_id": partner_id.id,
            "name": description,
            "clx_state": "new",
            "clx_sale_order_ids": self.sale_order_id.ids if self.sale_order_id.ids else False,
            "user_id": self.partner_id.account_user_id.id if self.partner_id.account_user_id else False,
            "clx_project_manager_id": cs_member,
            "intended_launch_date": launch_date,
            "deadline": max_date,
            "priority": self.priority,
            "clx_attachment_ids": self.clx_attachment_ids.ids,
        }
        return vals

    def _send_request_form_mail(self):
        web_base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        action_id = self.env.ref("project.open_view_project_all", raise_if_not_found=False)
        link = """{}/web#id={}&view_type=form&model=project.project&action={}""".format(
            web_base_url, self.project_id.id, action_id.id
        )
        context = self._context.copy() or {}
        context.update({"link": link})
        email_template = self.env.ref("clx_task_management.mail_template_request_form", raise_if_not_found=False)
        if email_template:
            email_template.with_context(context).send_mail(self.id, force_send=True)

    @api.onchange("intended_launch_date")
    def _onchange_intended_launch_date(self):
        if (
            self.max_proof_deadline_date and self.intended_launch_date
        ) and self.max_proof_deadline_date > self.intended_launch_date:
            self.intended_launch_date = self.max_proof_deadline_date
            raise UserError("Launch date must be equal or greated than project due date!")

    @api.onchange("request_line")
    def _onchange_request_line_type(self):
        if len(self.request_line) > 0:
            max_task_date = fields.Date.today()
            self.max_proof_deadline_date = fields.Date.today()

            for line in self.request_line:
                if hasattr(line, "req_type"):
                    # get the largest task date
                    if line.task_deadline and line.task_deadline > max_task_date:
                        max_task_date = line.task_deadline
                        self.max_proof_deadline_date = max_task_date

            if self.intended_launch_date and self.intended_launch_date < max_task_date:
                self.intended_launch_date = max_task_date

    @api.onchange("priority")
    def _onchange_priority(self):
        max_task_date = fields.Date.today()
        if len(self.request_line) > 0:
            self.max_proof_deadline_date = fields.Date.today()

        for line in self.request_line:
            if hasattr(line, "req_type"):
                today = fields.Date.today() if fields.Date.today() else datetime.datetime.today()
                current_day_with_time = self.write_date if self.write_date else datetime.datetime.today()
                user_tz = line.env.user.tz or "US/Pacific"
                current_day_with_time = timezone("UTC").localize(current_day_with_time).astimezone(timezone(user_tz))
                date_time_str = today.strftime("%d/%m/%y")
                date_time_str += " 14:00:00"
                comparsion_date = datetime.datetime.strptime(date_time_str, "%d/%m/%y %H:%M:%S")
                # if current_day_with_time after 2 pm:
                #     today + 1 day
                business_days_to_add = 0
                if current_day_with_time.time() > comparsion_date.time() or today.weekday() > 4:
                    business_days_to_add += 1

                if line.request_form_id.priority != "high":
                    business_days_to_add += 2

                if line.req_type in ("update", "budget"):
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
                    # get the largest task date
                    if current_date > max_task_date:
                        max_task_date = current_date
                        self.max_proof_deadline_date = max_task_date
                    else:
                        self.max_proof_deadline_date = current_date

                    # launch date must be >= proof deadline
                    if self.intended_launch_date and self.max_proof_deadline_date > self.intended_launch_date:
                        self.intended_launch_date = self.max_proof_deadline_date
                        # raise Message(_("Launch date was modified. It must be equal or greater than proofing deadling dates."))

                line.task_deadline = current_date

    def calculated_date(self, line):
        today = fields.Date.today()
        current_day_with_time = self.write_date
        user_tz = self.env.user.tz or "US/Pacific"
        current_day_with_time = timezone("UTC").localize(current_day_with_time).astimezone(timezone(user_tz))
        date_time_str = today.strftime("%d/%m/%y")
        date_time_str += " 14:00:00"
        comparsion_date = datetime.datetime.strptime(date_time_str, "%d/%m/%y %H:%M:%S")
        # if current_day_with_time after 2 pm:
        #     today + 1 day
        business_days_to_add = 0
        if current_day_with_time.time() > comparsion_date.time() or today.weekday() > 4:
            business_days_to_add += 1

        if line.request_form_id.priority != "high":
            business_days_to_add += 2

        if line.req_type in ("update", "budget"):
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
            # max_date = max(map(self.calculated_date,self.request_line))
            if self.intended_launch_date < self.max_proof_deadline_date:
                raise UserError("Please check Intended launch Date !!")

        project_id = False
        project_obj = self.env["project.project"]
        project_task_obj = self.env["project.task"]
        sub_task_obj = self.env["sub.task"]
        cl_task = self.env.ref("clx_task_management.clx_client_launch_sub_task_1", raise_if_not_found=False)
        if not self.description:
            raise UserError("Please add Project Title!!")
        if not self.request_line:
            raise UserError("There is no Request Line, Please add some line")
        if self.request_line and any(not line.description or not line.task_id for line in self.request_line):
            raise UserError(
                "Please add some Instruction on every line If do not have description Please delete that line."
            )

        subscriptions = self.env["sale.subscription"].search([("partner_id", "=", self.partner_id.id)])
        if not subscriptions:
            raise UserError("You can not submit request form there is no active sale for this customer!!")

        if self.description and self.partner_id:

            # Project creation is not allowed if there is already an open
            # project for this client. Popup a dialog and let the user know
            cs_member = False
            open_projects = self.env["project.project"].search(
                ["&", ("partner_id", "=", self.partner_id.id), ("clx_state", "!=", "done")]
            )
            if len(open_projects) > 0 and self.override_project_check:
                if open_projects.clx_project_manager_id:
                    cs_member = open_projects.clx_project_manager_id[0].id

            elif len(open_projects) > 0:
                context = dict(self._context or {})
                context["open_ids"] = open_projects.ids
                return {
                    "name": "Existing Project Warning",
                    "type": "ir.actions.act_window",
                    "res_model": "clx.existing.project.warning.wizard",
                    "view_mode": "form",
                    "target": "new",
                    "context": context,
                }

            vals = self.prepared_project_vals(self.description, self.partner_id, cs_member)
            if vals:
                project_id = project_obj.create(vals)

                if project_id:
                    project_id.req_form_id = self.id
                    self.project_id = project_id.id
                    self.assign_stage_project(project_id)

                    for line in self.request_line:
                        if line.task_id:
                            vals = self.prepared_task_vals(line, project_id)
                            main_task = project_task_obj.create(vals)

                            if main_task:
                                dependency_sub_tasks = sub_task_obj.search(
                                    [
                                        ("parent_id", "=", line.task_id.id),
                                        "|",
                                        ("dependency_ids", "=", False),
                                        ("dependency_ids", "=", cl_task and cl_task.id),
                                    ]
                                )
                                for sub_task in dependency_sub_tasks:
                                    vals = self.prepared_sub_task_vals(sub_task, main_task, line)
                                    project_task_obj.create(vals)

        if not self.intended_launch_date:
            self.intended_launch_date = self.max_proof_deadline_date

        self.state = "submitted"
        self.submitted_by_user_id = self.env.uid
        self._send_request_form_mail()

    @api.onchange("update_all_products")
    def _onchange_update_all_products(self):
        if self.update_all_products:
            self.cancel_client = False

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        self._generate_task_list()

    @api.onchange("cancel_client")
    def _onchange_cancel_client(self):
        list_product = []
        req_line_obj = self.env["request.form.line"]

        if self.cancel_client:
            # if client cancel request, set Project Title and hide other options.
            client_cancellation_main_task = self.env.ref("clx_task_management.client_cancellation_task")

            if self.partner_id.name:
                self.description = "CLIENT CANCELLATION - " + self.partner_id.name
            else:
                self.description = "CLIENT CANCELLATION"

            self.is_create_client_launch = False
            self.update_all_products = False
            self.cancel_user_id = self.partner_id.account_user_id.id

            cancellation_main_task_vals = {
                "req_type": client_cancellation_main_task.req_type,
                "task_id": client_cancellation_main_task.id,
                "requirements": client_cancellation_main_task.requirements,
                "description": client_cancellation_main_task.requirements,
            }
            form_line_id = req_line_obj.create(cancellation_main_task_vals)
            list_product.append(form_line_id.id)

            self.update(
                {
                    "request_line": [(6, 0, list_product)],
                    "product_ids": False,
                }
            )

        # Reset all cancellation fields if cancel deselected
        else:
            self.cancel_user_id = False
            self.cancel_client_type = False
            self.cancel_reports = False
            self.cancel_reason = False
            self.cancel_reason_detail = False
            self.cancel_service_date = False
            self.cancel_billing = False
            self.description = False

            if self.description and "CANCELLATION" in self.description:
                self.description = self.partner_id.name if self.partner_id.name else False

            self._generate_task_list()

    @api.onchange("is_create_client_launch")
    def _onchange_create_client_launch(self):
        list_product = []
        req_line_obj = self.env["request.form.line"]
        existing_lines = req_line_obj.search([("id", "in", self.request_line.ids)])
        request_products = self._generate_product_category_list()
        auto_tasks = (
            self.env.user.company_id.auto_add_main_task_ids
            if self.env.user.company_id and self.env.user.company_id.auto_add_main_task_ids
            else False
        )

        if self.is_create_client_launch:
            self.cancel_client = False
            list_product = self.request_line.ids

            for a_task in auto_tasks:
                vals = {
                    "req_type": a_task.req_type,
                    "task_id": a_task.id,
                    "requirements": a_task.requirements,
                    "description": a_task.requirements,
                }
                form_line_id = req_line_obj.create(vals)
                list_product.insert(0,form_line_id.id)
        else:
            for existing in existing_lines:
                if existing.task_id.id not in auto_tasks.ids:
                    list_product.append(existing.id)

        self.update({"request_line": [(6, 0, list_product)], "product_ids": request_products["product_ids"]})

        for line in self.request_line:
            line.update({"req_type": "new" if self.is_create_client_launch else "update"})

    def _generate_task_list(self):
        request_products = self._generate_product_category_list()
        self.update(
            {
                "request_line": [(6, 0, request_products["request_line"])]
                if request_products["request_line"]
                else False,
                "product_ids": request_products["product_ids"],
            }
        )

    def _generate_product_category_list(self):
        list_product = []
        req_line_obj = self.env["request.form.line"]
        lines = self.env["sale.order.line"].search([("order_partner_id", "=", self.partner_id.id)])
        order_lines = False
        product_ids = False

        if lines and not self.cancel_client:
            order_lines = lines
            order_lines = order_lines.filtered(lambda x: x.subscription_id.is_active and x.product_id.is_task_create)
            product_ids = order_lines.mapped("product_id") if order_lines else False

            for category in order_lines.mapped("product_id").mapped("categ_id"):
                line_id = req_line_obj.create(
                    {
                        "category_id": category.id,
                        "req_type": "update",
                    }
                )
                list_product.append(line_id.id)

        request_product = {"request_line": list_product if len(list_product) > 0 else False, "product_ids": product_ids}

        return request_product

    def update_description(self):
        for line in self.request_line:
            if self.update_products_des and self.update_all_products:
                if line.description and self.update_products_des not in line.description:
                    line.description += "\n \n" + self.update_products_des
                else:
                    line.description = self.update_products_des


class RequestFormLine(models.Model):
    _name = "request.form.line"
    _description = "Request Form Line"
    _rec_name = "request_form_id"
    _order = "create_date desc"

    request_form_id = fields.Many2one("request.form", string="Request Form", ondelete="cascade")
    req_type = fields.Selection([("new", "New"), ("update", "Update"), ("budget", "Budget")], string="Request Type")
    task_id = fields.Many2one("main.task", string="Task")
    task_deadline = fields.Date(string="Task Due Date", readonly=True, copy=False, compute="_default_task_deadline")
    description = fields.Text(string="Instruction", help="It will set as Task Description")
    requirements = fields.Text(string="Requirements")
    category_id = fields.Many2one("product.category", string="Products Category")

    def create_task_deadline_date(self):
        today = fields.Date.today()
        current_day_with_time = self.write_date or datetime.datetime.utcnow()
        user_tz = self.env.user.tz or "US/Pacific"
        current_day_with_time = timezone("UTC").localize(current_day_with_time).astimezone(timezone(user_tz))
        date_time_str = today.strftime("%d/%m/%y")
        date_time_str += " 14:00:00"
        comparsion_date = datetime.datetime.strptime(date_time_str, "%d/%m/%y %H:%M:%S")
        # if current_day_with_time after 2 pm:
        #     today + 1 day
        business_days_to_add = 0
        if current_day_with_time.time() > comparsion_date.time() or today.weekday() > 4:
            business_days_to_add += 1

        if self.request_form_id.priority != "high":
            business_days_to_add += 2

        if self.req_type in ("update", "budget"):
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

    def _default_task_deadline(taskLineArray):
        proof_deadline_date = taskLineArray.request_form_id.max_proof_deadline_date
        for taskLine in taskLineArray:
            taskLine.create_task_deadline_date()
            if not proof_deadline_date or taskLine.task_deadline > proof_deadline_date:
                taskLineArray.request_form_id.max_proof_deadline_date = taskLine.task_deadline

    @api.onchange("req_type")
    def _onchange_req_type(taskLine):
        taskLine.create_task_deadline_date()

    @api.onchange("task_id")
    def _onchange_task_id(self):
        if self.task_id:
            self.requirements = self.task_id.requirements
            self.description = self.task_id.requirements

    @api.onchange("req_type")
    def _onchange_main_task(self):
        if self.req_type and self.req_type == "update":
            subscriptions = self.env["sale.subscription"].search(
                [("partner_id", "=", self.request_form_id.partner_id.id)]
            )
            if not subscriptions:
                raise UserError(_("""There is no subscription available for this customer."""))
        if not self.category_id:
            return {"domain": {"task_id": [("req_type", "=", self.req_type), ("pull_to_request_form", "=", True)]}}
        elif self.category_id:
            return {
                "domain": {
                    "task_id": [
                        ("req_type", "=", self.req_type),
                        ("category_id", "=", self.category_id.id),
                        ("pull_to_request_form", "=", True),
                    ]
                }
            }
