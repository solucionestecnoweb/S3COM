{
    "name": "Custom Report Financiero",
    "version": "15.0",
    "summary": "Custom Report Financiero",
    "author": "David Cartaya",
    "license": "AGPL-3",
    "depends": ["base", "stock", "product", "sale", "mail", "purchase", "purchase_requisition", 'portal', 'crm', 'purchase_request', 'purchase_imports_extend', 'purchase_compare_multiple'],
    "data": [
        'views/res_partner.xml',
        'security/ir.model.access.csv',
        'views/stock_picking.xml',
        'views/purchase_requisition.xml',
        'views/template_date_pre_form.xml',
        'views/pre_requisition.xml',
        'views/sale_order.xml',
        'views/crm_sale_team.xml',
        'report/purchase_order.xml',
        'report/invoice_pro.xml',
        'data/mail_template_data.xml',
        'wizard/wizard_report_sale_order.xml'


    ],
    "installable": True,
    "auto_install": True,
    "application": False,
    'assets': {
        'web.assets_frontend': [
            '/custom_report_financiero/static/src/css/style.css',
        ],
        
    },
}