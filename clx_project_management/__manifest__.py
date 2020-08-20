# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
{
    'name': 'CLX Project Management',
    'version': '13.3.0.1',
    'summary': 'CLX Project Management',
    'sequence': 1,
    'description': """ CLX Project Management """,
    'category': '',
    'website': '',
    'depends': ['project',
                'sale_management',
                'sale_timesheet'],
    'data': [
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
