

{
    "name": "Product Variant Configurator",
    "summary": "Provides an abstract model for product variant configuration.",
    "category": "Product Variant",
    "development_status": "Production/Stable",
    "license": "AGPL-3",
    "author": "AvanzOSC, Tecnativa, ACSONE SA/NV, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/product-variant",
    "depends": ["product"],
    "data": [
        
        "views/product_configurator_attribute.xml",
       
    ],
    'assets': {
        'web.assets_backend': [
            'product_variant_configurator/static/src/js/sale_product_configurator_custom.js',
        ],
    },
}
