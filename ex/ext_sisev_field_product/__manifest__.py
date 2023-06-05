# -*- coding: utf-8 -*-
{
    'name': "Campos adicionales en ficha de productos",

    'summary': """Campos adicionales en ficha """,

    'description': """
       Campos adicionales en ficha 
       Colaborador: Ing. Darrell Sojo
    """,
    'version': '1.0',
    'author': 'INM&LDR Soluciones Tecnologicas',
    'category': 'Campos adicionales en ficha ',

    # any module necessary for this one to work correctly
    'depends': ['product','base', 'stock'],

    # always loaded
    'data': [
        'product_template_inherit.xml',
        'view_add.xml',
        'security/ir.model.access.csv',
    ],
    'application': True,
}
