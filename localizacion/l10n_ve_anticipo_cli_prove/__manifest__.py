{
    'name': "Localizacion Venezolana Modulo de Anticipo cliente / proveedor",

    'summary': """Localizacion Venezolana Modulo de Anticipo cliente / proveedor""",

    'description': """
       Ejecuta tambien los anticipos de pagos

    """,
    'version': '2.0',
    'author': 'INM & LDR Soluciones Tecnológicas y Empresariales C.A',
    'category': 'Tools',
    'website': 'http://soluciones-tecno.com/',

    # any module necessary for this one to work correctly
    'depends': ['base','account','account_accountant','payment'],

    # always loaded
    'data': [
    'vista/res_partner_view.xml',
    'vista/account_payment_view.xml',
    'vista/account_move_view.xml',
    'reporte/recibo_pago.xml',
    #'vista/res_company_view.xml',
    'security/ir.model.access.csv',
    #'vista/account_journal_views.xml',
    ],
    'application': True,
}
