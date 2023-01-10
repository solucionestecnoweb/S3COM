# -*- coding: utf-8 -*-
{
        'name': ' Venezuela - Account Sequence Number',
        'version': '14.0.1.0',
        'author': 'INM & LDR Soluciones Tecnológicas y Empresariales C.A',
        'maintainer': "Bryan Gómez <bryan.gomez1311@gmail.com>",
        'contributors': "Bryan Gómez <bryan.gomez1311@gmail.com>",
        'summary': '',
        'description': """""",
        'category': 'Accounting/Accounting',
        'website': 'http://soluciones-tecno.com/',
        'depends': ['account', 'account_debit_note'],
        'data': [
                'data/ir_sequence.xml',
                'views/account_move_views.xml',
                'views/res_config_settings_views.xml',
                'views/account_journal_views.xml',
        ],
        'license': 'LGPL-3',
        'installable': True,
        'application': True,
        'auto_install': False,
                      
}
