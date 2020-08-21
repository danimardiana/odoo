# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
{
    'name': 'Budget Analysis Report',
    'version': '13.3.0.2',
    'summary': 'Budget Analysis Report',
    'sequence': 1,
    'description': """ Budget Analysis Report """,
    'category': '',
    'website': '',
    'depends': ['clx_budget_management'],
    'data': [
        "security/ir.model.access.csv",
        "report/sale_budget_report.xml",

    ],
    'demo': [
    ],
    'qweb': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
