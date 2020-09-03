# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
{
    'name': 'CLX Task Management',
    'version': '13.3.0.0.4',
    'summary': 'CLX Task Management',
    'sequence': 1,
    'description': """ CLX Task Management """,
    'category': '',
    'author': 'CLx Media',
    'website': 'https://conversionlogix.com/',
    'depends': ['sale',
                'project'
                ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'data/task_stages.xml',
        'views/main_task_views.xml',
        'views/team_views.xml',
        'views/sub_task_views.xml',
        'views/request_form_views.xml',
        'views/project_views.xml'
    ],
    'demo': [
    ],
    'qweb': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
