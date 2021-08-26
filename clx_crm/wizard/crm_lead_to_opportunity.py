# -*- coding: utf-8 -*-
# Conversion Logix

from odoo import api, fields, models


class Lead2OpportunityPartner(models.TransientModel):
    _name = "crm.lead2opportunity.partner"
    _description = "Partner linking/binding in CRM wizard"
    _inherit = "crm.lead2opportunity.partner"

    @api.model
    def default_get(self, fields):
        result = super(Lead2OpportunityPartner, self).default_get(fields)

        if self._context.get("active_id"):
            tomerge = {int(self._context["active_id"])}

            partner_id = result.get("partner_id")
            lead = self.env["crm.lead"].browse(self._context["active_id"])
            email = lead.partner_id.email if lead.partner_id else lead.email_from

            tomerge.update(self._get_duplicated_leads(partner_id, email, include_lost=True).ids)

            result["action"] = "create"
            result["name"] = "convert"

            if lead.user_id:
                result["user_id"] = lead.user_id.id
            if lead.team_id:
                result["team_id"] = lead.team_id.id

        return result
