# -*- coding: utf-8 -*-
{
        'name': ' Venezuela - Sucursal Sale',
        'version': '14.0.1.0',
        'author': 'INM & LDR Soluciones Tecnológicas y Empresariales C.A',
        'contribuitors': "Bryan Gómez <bryan.gomez1311@gmail.com>",
        'summary': '',
        'description': """""",
        'category': 'Sale',
        'website': 'http://soluciones-tecno.com/',
        'depends': [
                'l10n_ve_sucursal',
                'l10n_ve_sucursal_stock',
                'l10n_ve_sucursal_account_analytic',
                'sale_stock',
                'sale'
        ],
        'data': ['views/sale_order_views.xml'],
        'license': 'LGPL-3',
        'installable': True,
        'application': True,
        'auto_install': False,
                      
}
