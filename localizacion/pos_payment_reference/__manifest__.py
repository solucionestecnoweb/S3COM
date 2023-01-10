# -*- coding: utf-8 -*-

{
    'name': 'POS Payment Reference',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'summary': 'POS Payment Reference',
    'description': """

""",
    'depends': ['point_of_sale'],
    'data': [
        'views/views.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            '/pos_payment_reference/static/src/js/pos.js',
        ],
        'web.assets_qweb': [
            'pos_payment_reference/static/src/xml/**/*',
        ],
    },
    'images': [
        'static/description/refer.jpg',
    ],
    'installable': True,
    'auto_install': False,
}
