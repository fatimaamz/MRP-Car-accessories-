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
        while current_page.has_next_page():
            next_url = current_page.next_page_url
            current_page = shopify.Product.find(from_=next_url)
            self._create_jobs_for_products(current_page)
            self._cr.commit()
            sleep(60)

    def _create_jobs_for_products(self, products):
        for product in products:
            self.process_single_product(product.id)
            self._cr.commit()

    def process_single_product(self, product_id):
        _logger.info("Start processing product")
        product = shopify.Product.find(product_id)
        existing_product = self.env['merket.connector.products.data.queue'].search([('shopify_id', '=', product.id)], limit=1)
        if not existing_product:
            _logger.debug(existing_product)
            return self.env['merket.connector.products.data.queue'].shopify_product_data_queue_create(product)
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
            
    