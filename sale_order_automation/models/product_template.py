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
            # Extract the reference (SKU) from the product name
            reference = product.name.split('#')[-1].strip()

            # Shopify API URL to fetch all products
            shopify_url = 'https://designer-trim.myshopify.com/products.json'
            _logger.info(f"Fetching Shopify product for SKU: {reference}")
            
            headers = {
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": "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"
            }

            # Fetch all products from Shopify
            response = requests.get(shopify_url, headers=headers)
            if response.status_code == 200:
                products = response.json().get('products', [])
                matching_product = None

                # Find the first simple product with the matching SKU
                for shopify_product in products:
                    # Check if the product is a simple product (i.e., not a variant)
                    if not shopify_product.get('variants'):
                        continue  # Skip products with variants

                    for variant in shopify_product['variants']:
                        if variant.get('sku') == reference:
                            matching_product = shopify_product
                            break
                    if matching_product:
                        break

                if matching_product:
                    # Process the first simple product found with the matching SKU
                    if matching_product['images']:
                        # Get the first image of the first product found
                        first_image_url = matching_product['images'][0]['src']
                        
                        # Download the first image from Shopify
                        img_data = requests.get(first_image_url).content
                        
                        # Update the image in Odoo (image_1920 field for the product image)
                        product.image_1920 = base64.b64encode(img_data)
                        
                        _logger.info(f"Updated image for product {product.name} (Reference: {reference})")
                    else:
                        _logger.warning(f"No images found for Shopify product with SKU {reference}.")
                else:
                    _logger.warning(f"No matching simple products found in Shopify for SKU {reference}.")
            else:
                _logger.error(f"Failed to fetch Shopify product for SKU {reference}: {response.status_code}")
