from odoo import api, fields, models


class CrmLeadContact(models.Model):
    _name = "crm.lead.contact"
    _description = "CRM Lead Contact"

    crm_lead_id = fields.Many2one("crm.lead", string="CRM Lead")
    name = fields.Char(string="Name")
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")
