# -*- coding: utf-8 -*-
{
    'name': 'Budget Analysis Report',
    'version': '13.3.0.1',
    'summary': 'Budget Analysis Report',
    'sequence': 1,
    'description': """ Budget Analysis Report """,
    'category': '',
    'website': '',
    'depends': ['clx_budget_management'],
    'data': [
        "security/ir.model.access.csv",
        "report/sale_budget_report.xml",
        "views/res_config_settings_views.xml"

    ],
    'demo': [
    ],
    'qweb': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}