# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, api


class Project(models.Model):
    _inherit = 'project.project'

    sale_order_id = fields.Many2one('sale.order', 'Sales Order',
                                    domain="[('partner_id', '=', partner_id)]", readonly=True,
                                    copy=False, help="Sales order to which the project is linked.")


class ProjectTask(models.Model):
    _inherit = "project.task"

    @api.model
    def _default_sale_line_id(self):
        sale_line_id = False
        if self._context.get('default_parent_id'):
            parent_task = self.env['project.task'].browse(self._context['default_parent_id'])
            sale_line_id = parent_task.sale_line_id.id
        if not sale_line_id and self._context.get('default_project_id'):
            project = self.env['project.project'].browse(self.env.context['default_project_id'])
            if project.billable_type != 'no':
                sale_line_id = project.sale_line_id.id
        return sale_line_id

    sale_line_id = fields.Many2one('sale.order.line', 'Sales Order Item',
                                   default=_default_sale_line_id,
                                   domain="[('is_service', '=', True), ('order_partner_id', '=', partner_id), ('is_expense', '=', False), ('state', 'in', ['sale', 'done'])]",
                                   help="Sales order item to which the task is linked. If an employee timesheets on a this task, "
                                        "and if this employee is not in the 'Employee/Sales Order Item Mapping' of the project, the "
                                        "timesheet entry will be linked to this sales order item.",
                                   copy=False)
    sale_order_id = fields.Many2one('sale.order', 'Sales Order', compute='_compute_sale_order_id',
                                    store=True, readonly=False,
                                    help="Sales order to which the task is linked.")
    billable_type = fields.Selection([
        ('task_rate', 'At Task Rate'),
        ('employee_rate', 'At Employee Rate'),
        ('no', 'No Billable')
    ], string="Billable Type", compute='_compute_billable_type', compute_sudo=True, store=True)

    @api.depends('sale_line_id', 'project_id', 'billable_type')
    def _compute_sale_order_id(self):
        for task in self:
            if task.billable_type == 'task_rate':
                task.sale_order_id = task.sale_line_id.sudo().order_id or task.project_id.sale_order_id
            elif task.billable_type == 'employee_rate':
                task.sale_order_id = task.project_id.sale_order_id
            elif task.billable_type == 'no':
                task.sale_order_id = False

    @api.depends('project_id.billable_type', 'sale_line_id')
    def _compute_billable_type(self):
        for task in self:
            billable_type = 'no'
            if task.project_id.billable_type == 'employee_rate':
                billable_type = task.project_id.billable_type
            elif (task.project_id.billable_type in ['task_rate',
                                                    'no'] and task.sale_line_id):  # create a task in global project (non billable)
                billable_type = 'task_rate'
            task.billable_type = billable_type
