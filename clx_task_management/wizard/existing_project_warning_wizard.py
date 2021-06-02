from odoo import api, fields, models


class ExistingProjectWarningWizard(models.TransientModel):
    _name = "clx.existing.project.warning.wizard"
    _description = "List of client projects that are open."

    name = fields.Char(string="Name", readonly=True)
    message = fields.Char(string="Message", readonly=True)

    def open_existing_project():
        print("Open Existing Project")

        return True
