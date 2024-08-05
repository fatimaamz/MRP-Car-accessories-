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
        'views/update_price_wizard.xml',
        'views/account_move_form_view.xml',
        'views/invoice_Nissan_edi.xml',
        'views/invoice_huyndai_edi.xml'
    ],
    'installable': True,


}   
