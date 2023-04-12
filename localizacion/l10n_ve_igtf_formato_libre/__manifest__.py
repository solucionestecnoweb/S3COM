{
    'name': "Localizacion Venezolana calculo de IGTF Formato libre",

    'summary': """Retención automática de ITF Formato libre""",

    'description': """
       Calcule la retención automática de itf para proveedores y para clientes.

    """,
    'version': '2.0',
    'author': 'INM & LDR Soluciones Tecnológicas y Empresariales C.A',
    'category': 'Tools',
    'website': 'http://soluciones-tecno.com/',

    # any module necessary for this one to work correctly
    'depends': ['base','account','l10n_ve_account','l10n_ve_account_sequence_number'],

    # always loaded
    'data': [
    'vista/account_payment_method_inherid.xml',
    'vista/account_payment_view.xml',
    'vista/account_journal_views.xml',
    'vista/account_move_inherit.xml',
    'vista/account_igtf_payment.xml',
    'wizard/wizard.xml',
    'report/reporte_view.xml',
    'report/reporte_2_view.xml',
    'security/ir.model.access.csv',
    #'formatos/factura_libre.xml',
    ],
    'assets': {
        'web.report_assets_common': [
            'l10n_ve_igtf_formato_libre/static/src/css/style.css',
        ],
    },
    'application': True,
}
