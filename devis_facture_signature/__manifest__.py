# -*- coding: utf-8 -*-
{
    'name': "gestion parc automobile",

    'summary': """
        Purchase order lines""",

    'description': """
       Introduce a vehicle field within Purchase order lines and ensure its inclusion in receipt and invoice lines.
    """,


    'category': 'purchase',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [ 'account','sale'],

    # always loaded
    'data': [

        'views/personnalisation_devis.xml',

        'views/personnalisation_facture.xml',

    ],
    # only loaded in demonstration mode
    'demo': [

    ],
}
