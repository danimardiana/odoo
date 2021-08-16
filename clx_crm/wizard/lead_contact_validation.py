from re import S
from odoo import api, fields, models


class ClxLeadContactValidation(models.TransientModel):
    _name = "lead.contact.validation"
    _description = "CRM Lead Contact Validation"

    selected = fields.Boolean(string="Selected", default=False)
    crm_lead_contact_id = fields.Integer(string="Lead Contact Id")
    crm_lead_contact_name = fields.Char(string="Lead Contact Name")
    existing_res_partner_id = fields.Integer(string="Existing Contact Id")
    existing_name = fields.Char(string="Existing Contact Name")
    existing_function = fields.Char(string="Existing Contact Job Position")
    existing_email = fields.Char(string="Existing Contact Email")
    existing_phone = fields.Char(string="Existing Contact Phone")
    existing_city = fields.Char(string="Existing Contact City")
    existing_state = fields.Char(string="Existing Contact State")

    # @api.onchange("selected")
    def selected_changes(self):
        check_box_row_group = self.env["lead.contact.validation"].search([("create_date", "=", self.create_date)])

        for row in check_box_row_group:
            self.selected = True
            # self.update({"selected": False})

            if row.crm_lead_contact_id == self.crm_lead_contact_id and row.id != self.id:
                row.selected = False
                # row.update({"selected": False})

                print(row.crm_lead_contact_name)

        return {
            "type": "set_scrollTop",
        }