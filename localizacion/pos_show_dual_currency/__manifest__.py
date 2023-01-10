
{
    "name": """POS: Mostrar Dualidad de moneda""",
    "summary": """Agrega el precio de otra moneda en los productos en POS""",
    "category": "Point Of Sale",
    "version": "14.0.1.0.2",
    "application": False,
    'author': 'José Luis Vizcaya López',
    'company': 'INM & LDR Soluciones Tecnológicas y Empresariales C.A',
    'maintainer': 'Ing. Darrell Sojo',
    'website': 'http://soluciones-tecno.com/',
    "depends": ["point_of_sale", "stock"],
    "data": ["views/views.xml", "views/pos_payment_meth.xml"],
      'assets': {
        'point_of_sale.assets': [
            'pos_show_dual_currency/static/src/js/models.js',
            'pos_show_dual_currency/static/src/js/pos_show_currency.js',
            'pos_show_dual_currency/static/src/js/OrderWidget.js',
            'pos_show_dual_currency/static/src/js/PaymentScreen.js',
            'pos_show_dual_currency/static/src/css/pos.css'
        ],
        'web.assets_qweb': [
            'pos_show_dual_currency/static/src/xml/**/*',
        ],
    },

    # "qweb": ["static/src/xml/pos.xml"],
    #"license": "OPL-1",
    'images': [
        'static/description/thumbnail.png',
    ],
    "price": 10,
    "currency": "USD",
    "auto_install": False,
    "installable": True,
}
