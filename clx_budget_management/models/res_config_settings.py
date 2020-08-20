from odoo import fields, api, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    month_selection = fields.Selection([
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December'),
    ], string="Month for Sale Budget Creation")

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'budget_month', self.month_selection or False)
        return super(ResConfigSettings, self).set_values()

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            month_selection=str(params.get_param('budget_month', '')) or False
        )
        return res
