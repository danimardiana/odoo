# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
{
    'name': 'CLX Task Management',
    'version': '13.3.0.0.10',
    'summary': 'CLX Task Management',
    'sequence': 1,
    'description': """ CLX Task Management """,
    'category': '',
    'author': 'CLx Media',
    'website': 'https://conversionlogix.com/',
    'depends': ['sale',
                'project',
                'sale_management'
                ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'data/task_stages.xml',
        'data/team_data.xml',
        'data/main_task.xml',
        'data/client_launch_task.xml',
        'data/tcc_launch_sub_task.xml',
        'data/google_ads_launch_sub_task.xml',
        'data/bing_ads_launch_sub_task.xml',
        'data/retargeting_launch_sub_task.xml',
        'data/data_driven_sub_task.xml',
        'data/facebook_launch_sub_task.xml',
        'data/instagram_sub_task.xml',
        'data/facebook_and_instagram_sub_task.xml',
        'data/instagram_stories_sub_task.xml',
        'data/snapchat_story_sub_task.xml',
        'data/youtube_sub_task.xml',
        'data/live_chat_sub_task.xml',
        'data/conversion_driver_sub_task.xml',
        'data/prelease_landing_page_sub_task.xml',
        'data/Cooperative_landing_page_sub_task.xml',
        'data/email_sub_task.xml',
        'data/google_my_business_sub_task.xml',
        'views/main_task_views.xml',
        'views/team_views.xml',
        'views/sub_task_views.xml',
        'views/request_form_views.xml',
        'views/project_views.xml',
        'views/sale_order_views.xml',
        'wizard/task_cancel_warning_wizard_views.xml'
    ],
    'demo': [
    ],
    'qweb': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
