# -*- coding: utf-8 -*-
{
    'name': "Extencion Terminal Punto de Venta JS",

    'summary': """Extencion Terminal Punto de Venta JS""",

    'description': """
       EExtencion Terminal Punto de Venta JS
     
    """,
    'version': '1.0',
    'author': 'INM&LDR Soluciones Tecnologicas',

    # any module necessary for this one to work correctly
    'depends': ['base','point_of_sale'],

    # always loaded
    'data': [
            'views/pos_config.xml'
        ],

    'assets': {
        'point_of_sale.assets': [
            '/ext_tpdv/static/src/css/style.css',
            '/ext_tpdv/static/src/js/OrderlineCustomerNoteButtonNew.js',
            '/ext_tpdv/static/src/js/note_receipt.js',
            '/ext_tpdv/static/src/js/PaymentScreen.js'
        ],
        'web.assets_qweb': [
            'ext_tpdv/static/src/xml/**/*',
        ],
    },
    
    'application': True,
}
