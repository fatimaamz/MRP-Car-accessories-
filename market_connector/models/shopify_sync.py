import logging
import json
from time import sleep
from odoo import models, fields
from odoo import models, api
from ..libs  import shopify


_logger = logging.getLogger("Shopify Sync")

class ShopifySync(models.Model):
    _name = 'shopify.sync'
    _description = 'Shopify Synchronization'

    @api.model
    def sync_products(self, session):
        shopify.ShopifyResource.activate_session(session)
        current_page = shopify.Product.find()
        self._create_jobs_for_products(current_page)
        print("current_page",current_page.has_next_page())
        while current_page.has_next_page():
            next_url = current_page.next_page_url
            print("next_url",next_url)
            current_page = shopify.Product.find(from_=next_url)
            self._create_jobs_for_products(current_page)
            self._cr.commit()
            sleep(60)

    @api.model
    def scheduled_sync_products(self, name, to_odoo=False):
        credentials = self.env['shopify.credentials'].search([('name', '=', name)], limit=1)
        if not credentials:
            _logger.error("No Shopify credentials found")
            return False
            
        session = credentials.get_session()
        current_page = credentials.current_page
        # Sync products for the current page
        shopify.ShopifyResource.activate_session(session)
        try:
            products = shopify.Product.find(limit=50, page=current_page)
            if products:
                self._create_jobs_for_products(products, to_odoo)
                self._cr.commit()
                _logger.info(f"Synced page {current_page} with {len(products)} products")
                
                # Increment page number for next run
                next_page = current_page + 1
                credentials.current_page = next_page
            else:
                # If no products found, reset to page 1
                credentials.current_page = 1
                _logger.info("No products found, resetting to page 1")
            credentials._cr.commit()
        except Exception as e:
            _logger.error(f"Error during scheduled sync: {e}")
            
        return True

    def _create_jobs_for_products(self, products, to_odoo=False):
        for product in products:
            self.process_single_product(product.id, to_odoo)
            self._cr.commit()
            sleep(1)

    def process_single_product(self, product_id, to_odoo=False):
        _logger.info("Start processing product")
        product = shopify.Product.find(product_id)
        existing_product = self.env['merket.connector.products.data.queue'].search([('shopify_id', '=', product.id)], limit=1)
        if not existing_product:
            _logger.debug(existing_product)
            product_queue = self.env['merket.connector.products.data.queue'].shopify_product_data_queue_create(product)
            if to_odoo:
                product_queue.create_or_update()
        else:
            _logger.info(f"Product with ID {product.id} already exists in the queue, skipping.{existing_product}")
            return existing_product
        
    
    @api.model
    def get_order_by_id(self, order_id, session=None):
        if session:
            shopify.ShopifyResource.activate_session(session)
        try:
            order = shopify.Order.find(order_id)
            if order:
                _logger.info(f"Order ID {order_id} retrieved successfully.")
                return order.to_dict()
            else:
                _logger.warning(f"Order ID {order_id} not found.")
                return None
        except Exception as e:
            _logger.error(f"Failed to retrieve order ID {order_id}: {e}")
            return None
            
    @api.model
    def sync_products_batch(self, session, limit=50, page=1):
        """
        Synchronize products in batches
        :param session: Shopify session
        :param limit: Number of products per batch (default: 50)
        :param page: Page number to fetch (default: 1)
        """
        _logger.info(f"Starting batch sync - Page: {page}, Limit: {limit}")
        shopify.ShopifyResource.activate_session(session)
        
        try:
            products = shopify.Product.find(limit=limit, page=page)
            if products:
                self._create_jobs_for_products(products)
                self._cr.commit()
                return len(products)  # Return number of processed products
            return 0
        except Exception as e:
            _logger.error(f"Error during batch sync: {e}")
            return 0

    @api.model
    def cron_sync_products(self, limit=50):
        """
        Cron job method to sync products
        :param limit: Number of products per batch
        """
        credentials = self.env['shopify.credentials'].search([], limit=1)
        if not credentials:
            _logger.error("No Shopify credentials found")
            return False

        session = credentials.get_session()
        page = 1
        total_processed = 0

        while True:
            processed_count = self.sync_products_batch(session, limit, page)
            if processed_count == 0:  # No more products to process
                break
                
            total_processed += processed_count
            _logger.info(f"Processed {total_processed} products so far")
            page += 1
            sleep(60)  # Respect Shopify API rate limits

        _logger.info(f"Completed sync of {total_processed} products")
        return True
            
    