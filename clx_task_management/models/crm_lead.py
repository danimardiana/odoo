# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def action_sale_quotations_new(self):
        res = super(CrmLead, self).action_sale_quotations_new()
        won_stage_id = self.env.ref('crm.stage_lead4')
        if won_stage_id and self.stage_id != won_stage_id:
            raise UserError(_("You will need WON stage to create Quotation."))
        return res
