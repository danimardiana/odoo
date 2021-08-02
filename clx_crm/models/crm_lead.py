# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    lead_company_type = fields.Selection(
        string="Lead Company Type",
        selection=[
            ("person", "Individual"),
            ("company", "Customer Company"),
            ("owner", "Owner"),
            ("management", "Management"),
        ],
        default="company",
    )
    crm_lead_contact_ids = fields.One2many("crm.lead.contact", "crm_lead_id", string="Lead Contact")

    # Overriding this method so that commercial_partner_id.id (the company) is used to create the
    # lead company customer rather than default partner.id, which is the lead contact/person
    def handle_partner_assignation(self, action="create", partner_id=False):
        """Handle partner assignation during a conversion from lead to opportunity.
        if action is 'create', create new partner with contact and assign lead to new partner_id.
        otherwise assign lead to the specified partner_id

        :param list ids: leads/opportunities ids to process
        :param string action: what has to be done regarding partners (create it, assign an existing one, or nothing)
        :param int partner_id: partner to assign if any
        :return dict: dictionary organized as followed: {lead_id: partner_assigned_id}
        """
        partner_ids = {}
        for lead in self:
            if partner_id:
                lead.partner_id = partner_id
            if lead.partner_id:
                partner_ids[lead.id] = lead.partner_id.id
                continue
            if action == "create":
                partner = lead._create_lead_partner()
                partner_id = partner.commercial_partner_id.id
                partner.team_id = lead.team_id
            partner_ids[lead.id] = partner_id
        return partner_ids

    @api.onchange("name")
    def onchange_lead_name(self):
        self.partner_name = self.name
