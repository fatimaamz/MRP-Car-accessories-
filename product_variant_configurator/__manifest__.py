{
    'name': 'Sale Product Configurator Customizations',
    'version': '1.0',
    'category': 'Sales',
    'depends': ['sale_product_configurator', 'web'],
    'data': [
        'views/sale_product_configurator_custom.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'product_variant_configurator/static/src/js/sale_product_configurator_custom.js',
        ],
    },
    'installable': True,
}
