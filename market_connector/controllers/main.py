import json
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger("Shopify Controller")

class CustomMain(http.Controller):
    
    @http.route(['/get_customer', '/update_customer'], csrf=False,method=["POST"], auth="public", type="json")
    def customer_create_or_update_webhook(self):

        webhook_route = request.httprequest.path.split('/')[1]
        res, instance = self.get_basic_info(webhook_route)
        if not res:
            return
        self.customer_webhook_process(res, instance)
        return
    
    def customer_webhook_process(self, response, instance):
        process_import_export_model = request.env["market.connector.shopify.import.export"].sudo()
        process_import_export_model.webhook_customer_create_process(response, instance)
        return True
    
    @http.route("/market-connector", csrf=False, auth="public", methods=["GET"])
    def version(self, **kwargs):
        return "1.0.01"
    
    @http.route("/get_order_data", csrf=False, auth="public", type="json")
    def handle_order_webhook(self):
        res, instance = self.get_basic_info("get_order_data")
        if not res:
            return
        

        _logger.info("UPDATE ORDER WEBHOOK call for order: %s", res.get("name"))
        

        fulfillment_status = res.get("fulfillment_status") or "unfulfilled"
        if request.env["sale.order"].sudo().search_read([("shopify_order_id", "=", res.get("id")),
                                                         ("shopify_order_number", "=",
                                                          res.get("order_number"))],
                                                        ["id"]):
            request.env["sale.order"].sudo().process_shopify_order_via_webhook(res, instance, True)
        elif fulfillment_status in ["fulfilled", "unfulfilled","pending"]:
            res["fulfillment_status"] = fulfillment_status
            request.env["sale.order"].sudo().process_shopify_order_via_webhook(res, instance)
        return

    def get_basic_info(self, route):
        data = http.request.httprequest.data
        host = request.httprequest.headers.get("X-Shopify-Shop-Domain")
        _logger.info(host)
        data_string = data.decode('utf-8')
        json_data = json.loads(data_string)
        _logger.info(json_data)
        instance = request.env['shopify.credentials'].sudo().search([("shopify_host", "ilike", host)], limit=1)
        return json_data, instance
