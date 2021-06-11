from odoo import api, fields, models


class ExistingProjectWarningWizard(models.TransientModel):
    _name = "clx.existing.project.warning.wizard"
    _description = "List of client projects that are open."

    title = fields.Char()
    message = fields.Char()
    open_project_ids = fields.Many2many("project.project")

    @api.model
    def default_get(self, fields):
        res = super(ExistingProjectWarningWizard, self).default_get(fields)
        open_ids = self._context["open_ids"]
        open_projects = self.env["project.project"].search([("id", "in", open_ids)])
        if len(open_projects) > 0:
            res.update(
                {
                    "message": "One or more projects is open for this customer. Please add any new task request to an existing project",
                    "open_project_ids": open_projects.ids,
                }
            )
        return res

    def _set_projects(self):
        self.open_existing_project = {}

    def open_existing_project(self):
        print("Open Existing Project")
        return True
