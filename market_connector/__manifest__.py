# -*- coding: utf-8 -*-
{
    'name': "Market Connector",
    'version': '17.0.0.1',
    'summary': """
        Market Connector
        """,

    'description': """
        Market Connector
    """,
    'license': 'OPL-1',
    'author': "WEELITE",
    'website': "https://weelite.co",
    'category': 'Sales',
    'depends': ['base', 'product', 'sale_management','common_connector_library'],
    'data':[
        'security/group.xml',
        'security/ir.model.access.csv',
        'views/shopify_credentials_view.xml',
        'views/sale_order_view.xml',
        'views/product_template_view.xml',
        'views/shopify_product_queue_view.xml',
        'views/shopify_order_queue_view.xml',
        'views/product_product.xml',
        'views/menu.xml',
        'views/order_data_queue_ept.xml',
    ],
    'images': ['static/src/description/icon.png']
}
