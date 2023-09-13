{
    'name': 'Venezuela - Account',
    'version': '15.0.1.0',
    'summary': '',
    'description': '',
    'category': 'Accounting/Accounting',
    'author': 'INM & LDR Soluciones Tecnológicas y Empresariales C.A',
    'contribuitors': "Bryan Gómez <bryan.gomez1311@gmail.com>",
    'website': 'http://soluciones-tecno.com/',
    'license': 'LGPL-3',
    'depends': ['l10n_ve_currency_rate', 'l10n_ve_base'],
    'data': [
        'views/account_move_views.xml',
        'views/account_move_line_views.xml',
        'views/account_payment_views.xml',
        'views/account_payment_register_views.xml',
        'views/pago.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False
}
