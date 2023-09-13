# -*- coding: utf-8 -*-
{
    'name': "Parche para modulo l10n_ve_account y l10n_ve_currency_rate",

    'summary': """Impresion Fiscal en ventas""",

    'description': """
      Parche para modulo l10n_ve_account y l10n_ve_currency_rate
      Colaboradores: Darrell Sojo
    """,
    'version': '1.0',
    'author': 'Ing. Darrell Sojo',
    'category': 'Tools',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account','l10n_ve_account'],

    # always loaded ...
    'data': [
        ##'security/ir.model.access.csv',
        ##'vista/account_invoice_config.xml',
        ##'vista/account_journal_views.xml',
        'vista/account_move.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo/demo.xml',
    ],
    'application': True,
}
