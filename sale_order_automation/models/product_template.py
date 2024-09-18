from odoo import api, fields, models, exceptions
import base64
import logging
import requests
_logger = logging.getLogger(__name__)

class ShopifyProductSync(models.Model):
    _inherit = 'product.template'

    def sync_selected_shopify_images(self):
        selected_records = self.browse(self.env.context.get('active_ids', []))
        for product in selected_records:
            
                # Shopify API details
                reference = product.name.split('#')[-1].strip()
                shopify_url = f'https://designer-trim.myshopify.com/products.json?sku={reference}'
                _logger.info(f" SKU {product.name} (SKU: {reference})")
                headers = {
                    "Content-Type": "application/json",
                    "X-Shopify-Access-Token": "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"
                }

                # Fetch the product from Shopify based on the SKU
                response = requests.get(shopify_url, headers=headers)
                if response.status_code == 200:
                    products = response.json().get('products', [])
                    for shopify_product in products[0]:
                        if shopify_product['images']:  # Check if the product has images
                            first_image_url = shopify_product['images'][0]['src']  # Get the first image URL
                            # Download the first image from Shopify
                            img_data = requests.get(first_image_url).content
                            # Update the image in Odoo (image_1920 field for the product image)
                            product.image_1920 = base64.b64encode(img_data)
                            _logger.info(f"Updated image for product {product.name} (Reference: {reference})")
                            # Stop after processing the first image
                            break
                else:
                    _logger.error(f"Failed to fetch Shopify product for SKU {product.default_code}: {response.status_code}")
