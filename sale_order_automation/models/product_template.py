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
            shopify_url = 'https://designer-trim.myshopify.com/products.json'
            _logger.info(f" SKU {product.name} (Reference: {reference})")
            headers = {
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": "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"
            }
    
            # Fetch all products from Shopify
            response = requests.get(shopify_url, headers=headers)
            if response.status_code == 200:
                products = response.json().get('products', [])
                
                # Filter product by SKU (manually)
                filtered_product = None
                for shopify_product in products:
                    if shopify_product.get('variants'):
                        for variant in shopify_product['variants']:
                            if variant.get('sku') == reference:
                                filtered_product = shopify_product
                                break
                    if filtered_product:
                        break
    
                if filtered_product and filtered_product['images']:  # Check if the product has images
                    first_image_url = filtered_product['images'][0]['src']  # Get the first image URL
                    # Download the first image from Shopify
                    img_data = requests.get(first_image_url).content
                    # Update the image in Odoo (image_1920 field for the product image)
                    product.image_1920 = base64.b64encode(img_data)
                    _logger.info(f"Updated image for product {product.name} (Reference: {reference})")
                else:
                    _logger.warning(f"No images found for product {product.name} (Reference: {reference}) or product not found.")
            else:
                _logger.error(f"Failed to fetch Shopify product for SKU {reference}: {response.status_code}")
