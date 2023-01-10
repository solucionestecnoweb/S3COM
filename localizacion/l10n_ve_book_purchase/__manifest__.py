# -*- coding: utf-8 -*-

{
    'name': 'Venezuela - Libro de Compras',
    'version': '14.0.1.0',
    'author': 'INM & LDR Soluciones Tecnológicas y Empresariales C.A',
    'contribuitors': "Bryan Gómez <bryan.gomez1311@gmail.com>",
    'category': 'Accounting/Accounting',
    'website': 'http://soluciones-tecno.com/',
    'license': 'LGPL-3',
    'depends': ['account', 'l10n_ve_account_tax_amount', 'l10n_ve_account', 'l10n_ve_resume_alicuota'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_book_purchase_views.xml',
        'views/book_menuitem.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False
}
