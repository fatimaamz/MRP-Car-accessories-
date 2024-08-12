import logging
import json
import time
from ..libs.pyactiveresource.connection import ClientError
from odoo import models, fields, api
from dateutil import parser
from datetime import datetime
from ..libs import shopify

_logger = logging.getLogger("Shopify Order")

class ShopifyProductDataQueueEpt(models.Model):
    _name = "merket.connector.products.data.queue"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    
    name = fields.Char(size=120) 
    is_process_queue = fields.Boolean("Is Processing Queue", default=False)
    shopify_id = fields.Char()
    shopify_title = fields.Char()
    shopify_name = fields.Char()
    shopify_years = fields.Char()
    shopify_attribute = fields.Char()
    shopify_reference = fields.Char()
    variant_id = fields.Char()
    data = fields.Char()
    product_id = fields.Many2one('product.product', string="Product", required=False)
    
    
    @api.model
    def create(self, vals):
        seq = self.env["ir.sequence"].next_by_code("merket.connector.customer.data.queue") or "/"
        vals.update({"name": seq or ""})
        return super(ShopifyProductDataQueueEpt, self).create(vals)
    
    @api.model
    def create_with_sql(self, vals):
        seq = self.env["ir.sequence"].next_by_code("merket.connector.customer.data.queue") or "/"
        vals.update({"name": seq})
        
        now = fields.Datetime.context_timestamp(self, datetime.now())
        
        # Prepare SQL query
        query = """
            INSERT INTO merket_connector_products_data_queue 
            (name, is_process_queue, shopify_id, shopify_title, shopify_name, shopify_years, shopify_attribute, shopify_reference, data, product_id, create_uid, create_date, write_uid, write_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """

        # Prepare values
        values = (
            vals.get('name'),
            vals.get('is_process_queue', False),
            vals.get('shopify_id'),
            vals.get('shopify_title'),
            vals.get('shopify_name'),
            vals.get('shopify_years'),
            vals.get('shopify_attribute'),
            vals.get('shopify_reference'),
            vals.get('data'),
            vals.get('product_id'),
            self.env.uid,  # create_uid
            now,           # create_date
            self.env.uid,  # write_uid
            now            # write_date
        )

        # Execute the SQL query
        self.env.cr.execute(query, values)
        result = self.env.cr.fetchone()

        # Return the newly created record as an Odoo recordset
        print(result)
        print(self.browse(result[0]) if result else None)
        return self.browse(result[0]) if result else None
    
    def shopify_product_data_queue_create(self, result):
        title = result.title
        split_title = [part.strip() for part in title.split('|')]
        try:
            name = split_title[0]
            years = split_title[1]
            attribute = split_title[2]
            reference = split_title[3]
            result = result.to_dict()
            data = json.dumps(result)
            self.create({
                    'shopify_id': result.get('id'),
                    'shopify_title': result.get('title'),
                    'shopify_name': name,
                    'shopify_years': years,
                    'shopify_attribute': attribute,
                    'shopify_reference': reference,
                    'data' : data
                })
        except IndexError:
            print(split_title)
        except Exception as err:
            print(err)
            
    def shopify_sync_products(self,shopify_id, instance):
        shopify_product = self.search([("shopify_id", "=", shopify_id)])
        if not shopify_product:
            # TODO : Fix le problème return None
            shopify_product =  self.new_signle_product(shopify_id, instance)
        return self.macthing_product(shopify_product)
    
    def macthing_product(self, shopify_product):
        product = self.env['product.product'].search([], limit=1)
        print("Matching product",shopify_product, product)
        shopify_product.product_id = product
        product.variant_id = shopify_product.shopify_id
        return product
        
        
    
    def new_signle_product(self,shopify_id, instance):
        instance.connect_in_shopify()
        shopify_product = self.env['shopify.sync'].process_single_product(shopify_id)
        # matching 
        return 
        