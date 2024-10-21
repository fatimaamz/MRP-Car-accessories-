# models/product_product.py

from odoo import models, fields

class ProductProduct(models.Model):
    _inherit = 'product.product'

    shopify_id = fields.Char(string='Shopify ID', help='ID of the product in Shopify')
    variant_id = fields.Char(string='Shopify Variante ID', help='ID of the product in Shopify')