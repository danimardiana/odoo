from odoo import api, fields, models


class ClientCancellationDetails(models.Model):
    _name = "client.cancellation.details"
    _description = "Client Cancellation Details"

    req_form_id = fields.Many2one("request.form", string="Request Form")
    last_day_of_service = fields.Date(string="Last Day of Service")
    user_id = fields.Many2one("res.users", string="Account Manager")
    preferred_client_type = fields.Selection(
        [
            ("other", "Other"),
            ("greystar", "Greystar"),
            ("ave5", "Avenue 5"),
        ],
        string="Preferred Client Type",
    )
    reason = fields.Selection(
        [
            ("stabilized_asset", "Stabilized Asset"),
            ("perf_issue", "Performance Issue"),
            ("loss_of_mgmt", "Loss of Management"),
            ("owner_dissatisfiled", "Ownership Dissatisfiled"),
            ("mgmt_dissatisfiled", "Management Dissatisfiled"),
            ("comp_loss", "Lost to a Competitor"),
            ("budget_constraints", "Budget Constraints"),
            ("term_notice", "Notice of Termination"),
            ("clx_other", "Other (CLX Lost Contract)"),
            ("na", "N/A"),
        ],
        string="Reason for Cancellation",
    )
    reason_detail = fields.Text(string="Reason for Cancellation")
    reports = fields.Selection(
        [
            ("delete_today", "Delete reporting today."),
            ("delete_weekly_today", "Delete weekly reports today. Delete monthly reports after final reports issue."),
            ("delete_after_final", "Delete reporting after final reports issue."),
        ],
        string="How Should We Handle Automated Reports",
    )
    billing = fields.Selection(
        [
            ("full_month", "Spend a full month's budget in the remaining month."),
            ("half_month", "Spend a 1/2 month's budget in the remaining prorated month."),
        ],
        string="How Should We Handle Final Billing",
    )
