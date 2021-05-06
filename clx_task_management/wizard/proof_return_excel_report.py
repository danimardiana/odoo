# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import base64
import io
import xlsxwriter


class ProofReturnExcelReport(models.TransientModel):
    _name = "proof.return.excel.report"
    _description = "proof return excel report"

    team_id = fields.Many2many("clx.team")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    @api.model
    def default_get(self, fields):
        result = super(ProofReturnExcelReport, self).default_get(fields)
        teams = self.env["clx.team"].search([])
        if teams:
            self.team_id = teams.ids
            result.update({"team_id": teams.ids})
        return result

    @api.onchange("start_date", "end_date")
    def onchange_date_validation(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError(_("Invalid date range."))

    def _get_task_proof_return_data(self):
        tasks = self.env["task.proof.return"].search([("team_id", "in", self.team_id.ids)])
        if self.start_date and self.end_date:
            tasks = self.env["task.proof.return"].search(
                [
                    ("team_id", "in", self.team_id.ids),
                    ("create_date", ">=", self.start_date),
                    ("create_date", "<=", self.end_date),
                ]
            )
        elif self.start_date and not self.end_date:
            tasks = self.env["task.proof.return"].search(
                [("team_id", "in", self.team_id.ids), ("create_date", ">=", self.start_date)]
            )
        return tasks

    def download_report(self):
        tasks = self._get_task_proof_return_data()
        fp = io.BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        worksheet = workbook.add_worksheet("Proof Return")
        header_format = workbook.add_format({"bold": True})
        row = 0
        worksheet.write(row, 0, "Project", header_format)
        worksheet.write(row, 1, "Task", header_format)
        worksheet.write(row, 2, "Sub Task", header_format)
        worksheet.write(row, 3, "Team", header_format)
        worksheet.write(row, 4, "Date", header_format)
        worksheet.write(row, 5, "Proof Count Number", header_format)
        row += 1
        col = 0
        for task in tasks:
            if task.proof_return_count > 0:
                worksheet.write(row, col, task.task_id.project_id.name)
                worksheet.write(
                    row, col + 1, task.task_id.parent_id.name if task.task_id.parent_id else task.task_id.name
                )
                worksheet.write(row, col + 2, task.task_id.name)
                worksheet.write(row, col + 3, task.team_id.team_name)
                worksheet.write(row, col + 4, task.create_date.strftime("%m/%d/%Y, %H:%M:%S"))
                worksheet.write(row, col + 5, task.proof_return_count)
                row += 1

        workbook.close()
        fp.seek(0)
        result = base64.b64encode(fp.read())
        attachment_obj = self.env["ir.attachment"]
        attachment_id = attachment_obj.create(
            {"name": "proof_return_count.xlsx", "display_name": "Proof Return Count.xlsx", "datas": result}
        )
        download_url = "/web/content/" + str(attachment_id.id) + "?download=True"

        return {
            "type": "ir.actions.act_url",
            "url": str(download_url),
            "target": "new",
            "nodestroy": False,
        }