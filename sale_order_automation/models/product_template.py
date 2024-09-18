from odoo import api, fields, models, exceptions
import base64
import logging
import requests
_logger = logging.getLogger(__name__)

class ShopifyProductSync(models.Model):
    _inherit = 'product.template'

    def sync_selected_shopify_images(self):
        # Get the selected records (active_ids) from the context
        selected_records = self.browse(self.env.context.get('active_ids', []))
        
        for product in selected_records:
            if product.name:  
                # Extract reference from product name
                reference = product.name.split('#')[-1].strip()
                shopify_url = 'https://designer-trim.myshopify.com/admin/api/products.json'
                headers = {
                    "Content-Type": "application/json",
                    "X-Shopify-Access-Token": "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"
                }

                # Fetch all products from Shopify
                response = requests.get(shopify_url, headers=headers)
                if response.status_code == 200:
                    products = response.json().get('products', [])
                    # Find the product variant that matches the SKU (reference)
                    for shopify_product in products:
                        for variant in shopify_product.get('variants', []):
                            if variant['sku'] == reference:
                                _logger.info(f"Found matching product for SKU: {reference}")
                                # Fetch only the first image for this product
                                if shopify_product['images']:
                                    first_image_url = shopify_product['images'][0]['src']
                                    # Download the first image from Shopify
                                    img_data = requests.get(first_image_url).content
                                    # Update the image in Odoo (image_1920 field for the product image)
                                    product.image_1920 = base64.b64encode(img_data)
                                    _logger.info(f"Updated image for product {product.name} (Reference: {reference})")
                                else:
                                    _logger.warning(f"No images found for product {product.name} (Reference: {reference})")
                                break
                else:
                    _logger.error(f"Failed to fetch Shopify products. Status code: {response.status_code}")
