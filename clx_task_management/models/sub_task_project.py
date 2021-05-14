# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, api, models


class SubTaskProject(models.Model):
    _name = "sub.task.project"
    _description = "Sub Task project"

    task_id = fields.Many2one("project.task", string="Task")
    sub_task_id = fields.Many2one("sub.task", string="Sub Task")
    sub_task_name = fields.Char(string="Sub Task Name")
    team_ids = fields.Many2many("clx.team", string="Teams")
    team_members_ids = fields.Many2many("res.users", string="Team Members")
    tag_ids = fields.Many2many("project.tags", string="Tags")
    stage_id = fields.Many2one("project.task.type", string="Stage")
    project_id = fields.Many2one("project", string="Project")

    # Analyst selected Client Launch Date
    # intended_launch_date = fields.Date(related="project_id.partner_id.intended_launch_date", string='Intended Launch Date', store=True)

    def redirect_task(self):
        if self.task_id:
            view_id = self.env.ref("project.view_task_form2").id
            return {
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "project.task",
                "target": "self",
                "res_id": self.task_id.id,
                "views": [[view_id, "form"]],
            }
