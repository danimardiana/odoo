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

    def save_contact_choices(self, contacts):
        lead_contact_table = self.env["crm.lead.contact"]

        for contact in contacts:
            lead_contact = lead_contact_table.search([("id", "=", contact.get("crm_lead_contact_id"))])
            lead_contact.update(
                {
                    "name": contact.get("existing_name"),
                    "existing_contact_id": contact.get("existing_res_partner_id"),
                    "function": contact.get("existing_function"),
                    "validated": True,
                }
            )
