# -*- coding: utf-8 -*-
{
    "name": " Venezuela - Currency Rate",
    "version": "14.0.1",
    'author': 'INM & LDR Soluciones Tecnológicas y Empresariales C.A',
    'contribuitors': "Bryan Gómez <bryan.gomez1311@gmail.com>",
    'category': 'Accounting/Accounting',
    "description": """""",
    "maintainer": "Bryan Gómez <bryan.gomez1311@gmail.com>",
    "website": "",
    'license': 'LGPL-3',
    "depends": ['product', 'account', 'purchase', 'sale', 'l10n_ve_base'],
    "data": [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/res_currency_rate_server_views.xml',
        'views/product_template_views.xml',
        'views/product_pricelist_views.xml',
        'views/product_attribute_views.xml',
        'views/account_move.xml',
        'views/sale_order.xml',
        'views/purchase_order.xml',
        #'views/exchange_rate.xml',
    ],
    'license': 'LGPL-3',
    'qweb': [
        'static/src/xml/systray.xml',
    ],
    'assets':{
        'web.assets_backend': [
            'l10n_ve_currency_rate/static/src/js/systray_theme_menu.js'
        ],'web.assets_qweb': [
            'l10n_ve_currency_rate/static/src/xml/**/*',
        ],
    },
    "installable": True,

}
