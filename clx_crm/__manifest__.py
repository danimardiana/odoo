{
    "name": "CLX CRM",
    "version": "1.0",
    "category": "Sales/CRM",
    "sequence": 5,
    "summary": "Track leads and close opportunities",
    "description": "",
    "website": "https://www.odoo.com/page/crm",
    "depends": [
        "crm",
    ],
    "data": ["security/ir.model.access.csv", "views/crm_lead_views.xml"],
    "demo": [],
    "css": ["static/src/css/crm.css"],
    "installable": True,
    "application": True,
    "auto_install": False,
}