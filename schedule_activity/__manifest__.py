# -*- coding: utf-8 -*-
# © 2020- Aktiv Software
# Part of Aktiv Software See LICENSE file for full copyright
# and licensing details
{
    'name': "Schedule Activity Dashboard",
    'author': "Aktiv Software",
    'summary': """
     Displays all schedule activities in dashbaord.
        """,

    'description':
    """
	Displays all schedule activities in dashbaord and from that dashboard you can update the status of that activity like activity is      done        or you can delete manually.
    """,
    'license': "OPL-1",
    'category': 'Extra Tools',
    'version': '13.0.1.0.2',
    'price': 75.00,
    'currency': "EUR",
    'depends': ['mail','crm'],
    'images': ['static/description/banner.jpeg'],
    'data': [
        'security/activity_security.xml',
        'views/activity_views.xml',
        'views/activity_dashboard.xml',
    ],
    'qweb': [
         'static/src/xml/activity_dashboard.xml'
    ],
}
