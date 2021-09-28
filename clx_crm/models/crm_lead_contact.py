from odoo import api, fields, models


class CrmLeadContact(models.Model):
    _name = "crm.lead.contact"
    _description = "CRM Lead Contact"

    crm_lead_id = fields.Many2one("crm.lead", string="CRM Lead")
    name = fields.Char(string="Name")
    function = fields.Char(string="Job Position")
    role = fields.Selection(
        [("1", "Normal"), ("2", "Proofing Contact"), ("3", "Reporting Contact"), ("4", "Billing Contact")],
        string="Contact Role",
    )
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")
    existing_contact_id = fields.Integer(string="Existing Contact Id")
    validated = fields.Boolean(string="Lead contact has been validated", default=False)

    @api.onchange("name", "email")
    def onchange_lead_name_email(self):
        self.update({"validated": False})
