# -*- coding: utf-8 -*-
{
    'name': "limit_item",

    'summary': """
        Limita el número de lineas de pedido en Venta y Facturación 
        Facturas Rectificativas y Factura de Debito
        """,

    'description': """Limita el número de lineas de pedido en Venta y Facturación 
        Facturas Rectificativas y Factura de Debito """
        
    ,

    'author': "Oscar Mora",
    'website': "",

    'category': 'Uncategorized',
    'version': '0.15',

    'depends': ['account', 'sale'],


    'data': [
        # 'security/ir.model.access.csv',
        'views/limit_item_sale_view.xml',
        'views/limit_item_account_view.xml',
        'views/res_company.xml',
    ],

    'demo': [

    ],
}
