from odoo import api, fields, models


class CrmLeadContact(models.Model):
    _name = "crm.lead.contact"
    _description = "CRM Lead Contact"

    crm_lead_id = fields.Many2one("crm.lead", string="CRM Lead")
    name = fields.Char(string="Name")
    function = fields.Char(string="Job Position")
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")
    validated = fields.Boolean(string="Lead contact has been validated", default=False)
