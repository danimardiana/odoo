# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('order_line.product_id.project_id')
    def _compute_tasks_ids(self):
        for order in self:
            order.tasks_ids = self.env['project.task'].search(
                [('sale_order_id', '=', order.id),
                 ('sale_line_id', '=', False)])
            order.tasks_count = len(order.tasks_ids)

    def create_sub_task(self, project_task, line, parent_task, stage_id):
        """
        This method is used for Create Sub Task for parent task
        Param 1 : project_task - Object of project.task
        Param 2 : line - Browsable object of Sale order line
        Param 3: parent_task - Browsable object of project.task
        Param 4 : stage_id - Browsable Object of project.task.type
        return : No return
        """
        if line and parent_task:
            sub_task = project_task.search([('sale_line_id', '=', line.id)])
            if not sub_task:
                project_task.create({
                    'project_id': parent_task.project_id.id,
                    'name': line.display_name,
                    'stage_id': stage_id.id if stage_id else False,
                    'parent_id': parent_task.id,
                    'sale_line_id': line.id,
                    'sale_order_id': line.order_id.id
                })

    def create_main_task(self, project_task, project, stage_id):
        """
        this method is used for Create Main task
        Param 1 : project_task - object of project.task
        Param 2 : project - Browsable object of Project
        Param 3 : stage_id - Browsable object of project.task.type
        Return : Browsable object of project.task
        """
        if project:
            task = project_task.search([('name', '=', self.name)])
            if not task:
                parent_task = project_task.create({
                    'project_id': project.id,
                    'name': self.name,
                    'stage_id': stage_id.id if stage_id else False,
                    'sale_order_id': self.id
                })
                return parent_task

    def _action_confirm(self):
        res = super(SaleOrder, self)._action_confirm()
        project_obj = self.env['project.project']
        project_task = self.env['project.task']
        project = project_obj.search([('partner_id', '=', self.partner_id.id)], limit=1)
        stage_id = self.env['project.task.type'].search([('name', '=', 'To Do')], limit=1)
        if not project:
            project = project_obj.create(
                {
                    'name': self.partner_id.name,
                    'partner_id': self.partner_id.id,
                    'sale_order_id': self.id,
                }
            )
        parent_task = self.create_main_task(project_task, project, stage_id)
        for line in self.order_line.filtered(
                lambda l: l.product_id.type == 'service' and l.product_id.recurring_invoice):
            self.create_sub_task(project_task, line, parent_task, stage_id)
        return res
