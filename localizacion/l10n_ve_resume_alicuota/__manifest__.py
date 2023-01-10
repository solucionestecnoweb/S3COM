# -*- coding: utf-8 -*-
{
        'name': ' Venezuela - Resume Alicuota',
        'version': '14.0.1.0',
        'author': 'INM & LDR Soluciones Tecnológicas y Empresariales C.A',
        'contribuitors': "Bryan Gómez <bryan.gomez1311@gmail.com>",
        'summary': '',
        'description': """""",
        'category': 'Accounting/Localizations/Account Charts',
        'website': 'http://soluciones-tecno.com/',
        'license': "LGPL-3",
        'depends': ['l10n_ve_iva_retention'],
        'data': [
                'security/ir.model.access.csv',
                'views/alicuota_views.xml',
                'views/account_move_views.xml',
                'views/account_tax_views.xml',
                # 'views/municipal_menuitem.xml',
        ],
        'installable': True,
        'application': True,
        'auto_install': False,
                      
}
