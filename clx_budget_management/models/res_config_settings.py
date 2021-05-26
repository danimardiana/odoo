# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, api, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    month_selection = fields.Selection(
        [
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
            ("4", "4"),
            ("5", "5"),
            ("6", "6"),
            ("7", "7"),
            ("8", "8"),
            ("9", "9"),
            ("10", "10"),
            ("11", "11"),
            ("12", "12"),
        ],
        string="Month for Budget Creation",
    )
    team_ids = fields.Many2many("clx.team", string="Teams")
    contract_management_fee_product = fields.Many2one("product.product", string="Setup Fee Product")

    @api.model
    def set_values(self):
        config_parameter = self.env["ir.config_parameter"].sudo()
        config_parameter.set_param(
            "budget_month",
            self.month_selection or False,
        )
        config_parameter.set_param(
            "contract_management_fee_product",
            self.contract_management_fee_product.id or False,
        )
        company_id = self.env.user.company_id
        if company_id:
            company_id.team_ids = self.team_ids.ids

        return super(ResConfigSettings, self).set_values()

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env["ir.config_parameter"].sudo()
        company_id = self.env.user.company_id
        team_list = []
        if company_id and company_id.team_ids:
            team_list = company_id.team_ids.ids or []
        contract_management_fee_product = int(params.get_param("contract_management_fee_product", False)) or False
        res.update(
            contract_management_fee_product=contract_management_fee_product,
            month_selection=str(params.get_param("budget_month", "")) or False,
            team_ids=team_list,
        )
        return res
