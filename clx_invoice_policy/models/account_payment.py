from odoo import fields,models,api,_

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    management_company_type_id = fields.Many2one(string='Mgmt. Company',related="partner_id.management_company_type_id",store=True)

