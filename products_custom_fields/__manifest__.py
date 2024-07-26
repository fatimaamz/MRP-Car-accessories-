{
    'name': 'Custom products fields for importation',
    "author": "Weelite/Fatima AMZIL",
    "website": "",
    'category': 'Extra Tools',
    'summary': '',
    'description': """
        New custom product fields 
    """,
    'depends': ['base','product','sale','account'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_view.xml',
        'views/custom_standard_invoice.xml',
    ],
    'installable': True,


}   
