# models/product_template.py

from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    shopify_id = fields.Char(string='Shopify ID', help='ID of the product in Shopify')
