import requests
import base64
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class ShopifyProductSync(models.Model):
    _inherit = 'product.template'

    # Add a button to the form view for syncing
    def sync_selected_shopify_images(self):
        for product in self:
            if product.name:  # Assuming 'default_code' holds the SKU
                # Shopify API details
                reference = product.name.split('#')[-1].strip()
                shopify_url = f'designer-trim.myshopify.com/products.json?sku={reference}'
                _logger.info(f" SKU {product.name} (SKU: {reference})")
                headers = {
                    "Content-Type": "application/json",
                    "X-Shopify-Access-Token": "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"
                }

                # Fetch the product from Shopify based on the SKU
                response = requests.get(shopify_url, headers=headers)
                if response.status_code == 200:
                    products = response.json().get('products', [])
                    for shopify_product in products:
                        for image in shopify_product['images']:
                            image_url = image['src']
                            # Download the image from Shopify
                            img_data = requests.get(image_url).content
                            # Update the image in Odoo (image_1920 field for the product image)
                            product.image_1920 = base64.b64encode(img_data)
                            # Log the sync status
                            _logger.info(f"Updated image for product {product.name} (SKU: {product.default_code})")
                else:
                    _logger.error(f"Failed to fetch Shopify product for SKU {product.default_code}: {response.status_code}")

