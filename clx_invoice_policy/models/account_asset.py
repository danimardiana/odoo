from odoo import api, fields, models, _

class AccountAsset(models.Model):
    _inherit = 'account.asset'

    account_move_id = fields.Many2one('account.move',string="Invoice",compute="_compute_get_move")
    partner_id = fields.Many2one('res.partner',string="Customer",related="account_move_id.partner_id")

    # asset_id
    def _compute_get_move(self):
        for rec in self:
            move_id = self.env['account.move'].search([('line_ids.asset_id','=',rec.id)],limit=1)
            rec.account_move_id = move_id and move_id.id

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

    def _get_first_depreciation_date(self,vals={}):
        if self.model_id:
            return super(AccountAsset, self)._get_first_depreciation_date()
        return self.first_depreciation_date

    @api.depends('original_move_line_ids', 'original_move_line_ids.account_id', 'asset_type')
    def _compute_value(self):
        super(AccountAsset, self)._compute_value()
        for record in self:
            total_credit = sum(line.credit for line in record.original_move_line_ids)
            total_debit = sum(line.debit for line in record.original_move_line_ids)
            if total_debit:
                record.original_value = min(total_debit,-total_debit) + max(total_credit,-total_credit)