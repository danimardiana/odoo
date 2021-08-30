from odoo import api, fields, models, _

class AccountAsset(models.Model):
    _inherit = 'account.asset'

    @api.onchange('model_id')
    def _onchange_model_id(self):
        model = self.model_id
        if model:
            super(AccountAsset, self)._onchange_model_id()
        else:
            self.method = 'linear'
            self.method_number = 1 # number of months
            self.method_period = '1' # 1 for Month and 12 for Year
            self.method_progress_factor = 0.3 #0.3 is default value of this field
            # self.prorata = model.prorata
            self.prorata_date = fields.Date.today()
            self.account_analytic_id = self.account_analytic_id.id
            self.analytic_tag_ids = [(6, 0, self.analytic_tag_ids.ids)]
            self.account_depreciation_id = self.account_depreciation_id
            self.account_depreciation_expense_id = self.account_depreciation_expense_id
            self.journal_id = self.journal_id