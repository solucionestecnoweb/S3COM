# -*- coding: utf-8 -*-

{
    'name': 'Venezuela - Libro Resume de Venta y Compra',
    'version': '14.0.1.0',
    'author': 'INM & LDR Soluciones Tecnológicas y Empresariales C.A',
    'contribuitors': "Bryan Gómez <bryan.gomez1311@gmail.com>",
    'category': 'Accounting/Accounting',
    'website': 'http://soluciones-tecno.com/',
    'license': 'LGPL-3',
    'depends': ['account', 'l10n_ve_resume_alicuota'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/account_book_resume_iva_views.xml',
        'views/book_menuitem.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False
}
