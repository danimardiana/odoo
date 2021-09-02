from odoo import fields,models,api,_

class AnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    _sql_constraints = [
        ('unique_vert_analytic', 'unique(vertical)',
         'There can be only one Analytic account with each vertical.'),
    ]

    vertical = fields.Selection(
        [("res", "RES"), ("srl", "SRL"), ("local", "Local"), ("auto", "Auto")], string="Vertical"
    )