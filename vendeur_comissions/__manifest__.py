# -*- coding: utf-8 -*-
{
    'name': "Partner Statement Report",

    'summary': """
       Partner Statement Report""",

    'description': """
         
    """,

    'author': "Fatima amzil",
    'website': "http://www.weelite.ma",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['sale','base','account'],

    # always loaded
    'data': [
        'views/views.xml',
        'security/ir.model.access.csv'


    ],

}
