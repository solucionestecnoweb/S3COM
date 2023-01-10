# -*- coding: utf-8 -*-

{
    'name': 'Venezuela - Libro Diario',
    'version': '14.0.1.0',
    'author': 'INM & LDR Soluciones Tecnológicas y Empresariales C.A',
    'contribuitors': "Bryan Gómez <bryan.gomez1311@gmail.com>",
    'category': 'Accounting/Accounting',
    'website': 'http://soluciones-tecno.com/',
    'license': 'LGPL-3',
    'depends': ['account', 'l10n_ve_res_config_settings_retentions'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/account_diary_book_views.xml',
        'report/paperformat.xml',
        'report/ir_action_report.xml',
        'views/report_diary_book.xml',
        'views/book_menuitem.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False
}
