# -*- coding: utf-8 -*-
{
    'name': "Modulo de reporte resumen iva Bueno",

    'summary': """Modulo de reporte resumen iva Bueno""",

    'description': """
       Modulo de reporte resumen iva Bueno
    """,
    'version': '3.0',
    'author': 'INM & LDR Soluciones Tecnológicas y Empresariales C.A',
    'category': 'Tools',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'account',
        'account_accountant',
        'l10n_ve_iva_retention',
        'libro_resumen_alicuota',
        #'isrl_retention',
    ],

    # always loaded
    'data': [
        'view/wizard.xml',
        'view/reporte_view.xml',
        'security/ir.model.access.csv',
        #'view/account_move_view.xml',
        #'view/comprobantes.xml',
    ],
    'application': True,
}
