# -*- coding: utf-8 -*-
{
    'name': 'POS Require Customer | POS Customer Mandatory',
    'version': '14.0',
    'author': 'Preway IT Solutions',
    "category": "Point Of Sale",
    "depends" : ["point_of_sale"],
    'summary': 'This module is allow to require customer on pos order | POS Customer required | Mandatory customer on pos order',
    'data': [
        "views/pos_config_view.xml",
    ],
    'assets': {
        'point_of_sale.assets': [
            '/pw_customer_required/static/src/js/PaymentScreen.js',
    
        ],
     
    },
    'price': 10.0,
    'currency': "EUR",
    'application': True,
    'installable': True,
    "images":["static/description/Banner.png"],
}
