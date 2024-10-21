import base64
import csv
import logging
import time

from datetime import datetime, timedelta
from io import StringIO, BytesIO

from odoo.exceptions import UserError
from odoo.tools.misc import split_every

from odoo import models, fields, api, _
from .. import shopify
from ..libs.shopify.pyactiveresource.connection import ClientError


class ShopifyProcessImportExport(models.TransientModel):
    _name = 'market.connector.shopify.import.export'
    
    shopify_operation = fields.Selection(
        [("sync_product", "Import Products"),
         ("sync_product_by_remote_ids", "Import Products - By Remote Ids"),
         ("import_customers", "Import Customers"),
         ("import_unshipped_orders", "Import Unshipped Orders"),
         ("import_shipped_orders", "Import Shipped Orders"),
         ("import_orders_by_remote_ids", "Import Orders - By Remote Ids"),
         ("update_order_status", "Update Order Shipping Status"),
         ("export_stock", "Export Stock"),
         ("import_stock", "Import Stock"),
         ("import_products_from_csv", "Import Products From CSV"),
         ("import_location", "Import Location"),
         ("import_payout_report", "Import Payout Report")], default="sync_product", string="Operation")
    
    orders_from_date = fields.Datetime(string="From Date")
    orders_to_date = fields.Datetime(string="To Date")
    
    
    def webhook_customer_create_process(self, res, instance):
        data_queue_obj = self.env['merket.connector.customer.data.queue']
        customer_queue_id = data_queue_obj.search([("record_created_from", "=", "webhook"), ("state", "=", "draft"),
                                                   ("shopify_instance_id", "=", instance.id)])
        if customer_queue_id:
            message = "Customer %s added into Queue %s." % (res.get("first_name"), customer_queue_id.name)
        else:
            customer_queue_id = data_queue_obj.create_customer_queue(instance, "webhook")
            message = "Customer Queue %s created." % customer_queue_id.name
        print(message)

        customer_queue_id.synced_customer_queue_line_ids.shopify_customer_data_queue_line_create(res, customer_queue_id)
        if len(customer_queue_id.synced_customer_queue_line_ids) == 50:
            customer_queue_id.synced_customer_queue_line_ids.sync_shopify_customer_into_odoo()
        return True