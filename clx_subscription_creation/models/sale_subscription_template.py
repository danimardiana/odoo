from odoo import fields,models,api,_

class sale_sub_template(models.Model):
    _inherit = 'sale.subscription.template'

    account_depreciation_expense_id = fields.Many2one('account.account',
          string='Deferred Revenue Account', company_dependent=True,
          domain="['&', ('deprecated', '=', False), ('company_id', '=', current_company_id)]")