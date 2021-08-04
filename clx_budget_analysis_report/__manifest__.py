# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
{
    "name": "Budget Analysis Report",
    "version": "13.3.0.0.40",
    "summary": "Budget Analysis Report",
    "sequence": 1,
    "description": """ Budget Analysis Report """,
    "category": "",
    "author": "CLx Media",
    "website": "https://conversionlogix.com/",
    "depends": ["clx_budget_management", "clx_subscription_creation"],
    "data": [
        # "data/schedulers.xml",
        "security/ir.model.access.csv",
        "wizard/budget_report_views.xml",
        "report/sale_budget_report.xml",
    ],
    "demo": [],
    "qweb": [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
