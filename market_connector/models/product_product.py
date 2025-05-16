# models/product_product.py

from odoo import models, fields, api

class ProductImage(models.Model):
    _name = 'product.image'
    _description = 'Product Image'

    product_id = fields.Many2one('product.product', string='Product', ondelete='cascade')
    image = fields.Image(string='Image', required=True)
    name = fields.Char(string='Description')
    is_default = fields.Boolean(string='Default Image', default=False)

    @api.onchange('is_default')
    def _onchange_is_default(self):
        if self.is_default:
            self.product_id.product_images.filtered(lambda img: img.id != self.id).write({'is_default': False})

    
    
class ProductProduct(models.Model):
    _inherit = 'product.product'

    shopify_id = fields.Char(string='Shopify ID', help='ID of the product in Shopify')
    variant_id = fields.Char(string='Shopify Variante ID', help='ID of the product in Shopify')
    product_images = fields.One2many('product.image', 'product_id', string='Product Images')
    default_image = fields.Image(string="Default Image", compute='_compute_default_image')
    handle = fields.Char(string='Handle', help='Handle of the product in Shopify')

    @api.depends('product_images.is_default')
    def _compute_default_image(self):
        for product in self:
            default_image = product.product_images.filtered(lambda img: img.is_default)
            if len(default_image) > 1:
                # If somehow multiple default images exist, ensure only one is set as default
                default_image[1:].write({'is_default': False})
            product.default_image = default_image[0].image if default_image else False
            