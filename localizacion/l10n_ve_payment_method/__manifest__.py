# -*- coding: utf-8 -*-
{
    'name': ' Venezuela - Metodos de pagos',
    'version': '1.0',
    'category': 'Accounting/Accounting',
    'summary': 'Metodos de pagos',
    'description': """""",
    'author': 'INM & LDR Soluciones Tecnológicas y Empresariales C.A',
    'contribuitors': "Bryan Gómez <bryan.gomez1311@gmail.com>",
    'website': 'https://www.odoo.com/page/accounting',
    'depends': ['account'],
    'data': [
        'data/account_data.xml',
        'views/account_payment_method_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': True,
}
