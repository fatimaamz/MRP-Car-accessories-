import ast
import logging
import json
import time
from ..libs.pyactiveresource.connection import ClientError
from odoo import models, fields, api


_logger = logging.getLogger("Shopify Order Queue")

class ShopifyOrderQueue(models.Model):
    _name = "merket.connector.orders.data.queue"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    synchronized = fields.Boolean("Syncronisé", default=False)
    instance = fields.Many2one("shopify.credentials", "Compte", copy=False)
    shopify_id = fields.Char()
    data = fields.Char()
    logs = fields.Char()
    
    
    
    def add_logs(self,message):
        self.logs += f"{message} \n"
        
    
    def process_shopify_orders_directly(self, order_data, instance,manuel=False):
        common_log_book_obj = self.env["common.log.book.ept"]
        common_log_lines_obj = self.env["common.log.lines.ept"]

        model_id = common_log_lines_obj.get_model_id("sale.order")
        log_book = common_log_book_obj.create({"type": "import",
                                               "shopify_instance_id": instance.id,
                                               "module": "shopify_ept",
                                               "model_id": model_id})
        if not manuel:
            for order in order_data:
                self.create({
                    'shopify_id' : order.get('id','no-ref'),
                    'instance' : instance.id,
                    'data': order
                })
                self._cr.commit()
        sale_order_obj = self.env["sale.order"]
        order_ids = sale_order_obj.import_shopify_orders(order_data,log_book, is_queue_line=False)
        if not log_book.log_lines:
            log_book.unlink()
        return order_ids
    
    def update_order(self, order_data):
        self.data = order_data
        order_sale = self.env['sale.order'].search([('shopify_order_id',"=",order_data.get("id"))],limit=1)
        order_sale.shopify_order_status = order_data.get("fulfillment_status") or "unfulfilled"
        fulfillments = order_data.get('fulfillments',[])
        if len(fulfillments)>0:
            print(fulfillments[0].get("tracking_company"),fulfillments[0].get("tracking_number"),fulfillments[0].get("shipping_status"))
            order_sale.tracking_company = fulfillments[0].get("tracking_company")
            order_sale.tracking_number = fulfillments[0].get("tracking_number")
            order_sale.shipping_status = fulfillments[0].get("shipping_status")
        return True
        
    
    def force_sync(self):
        for record in self:
            if record.instance:
                if record.data:
                    data_dict = ast.literal_eval(record.data)
                else:
                    record.instance.connect_in_shopify()
                    data_dict = self.env['shopify.sync'].get_order_by_id(record.shopify_id)
                    record.data = data_dict
                    self._cr.commit()
                self.env['sale.order'].sudo().process_shopify_order_via_webhook(data_dict, record.instance,manuel=True)
        
    
    