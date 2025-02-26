import json
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
from ..libs.pyactiveresource.connection import ForbiddenAccess
from ..libs  import shopify
import qrcode
import base64
import io
import logging

_logger = logging.getLogger(__name__)

class ShopifyCredentials(models.Model):
    _name = 'shopify.credentials'
    _description = 'Shopify Credentials'

    name = fields.Char(string='Name', required=True, help="A name to identify the credentials")
    api_key = fields.Char(string='API Key', required=True)
    api_secret = fields.Char(string='API Secret', required=True)
    shop_url = fields.Char(string='Shop URL', required=True, help="Example: https://your-shop-name.myshopify.com")
    access_token = fields.Char(string='Access Token', required=True)
    last_sync_date = fields.Datetime(string='Last Sync Date', readonly=True)
    shopify_store_time_zone = fields.Char("Store Time Zone",
                                          help='This field used to import order process')
    shopify_company_id = fields.Many2one('res.company', string='Company', required=True,
                                         default=lambda self: self.env.company)
    shipping_product_id = fields.Many2one("product.product", domain=[('type', '=', 'service')],
                                          help="This is used for set shipping product in a Carrier.")
    discount_product_id = fields.Many2one("product.product", "Discount",
                                          domain=[('type', '=', 'service')],
                                          help="This is used for set discount product in a sale order lines")
    apply_tax_in_order = fields.Selection(
        [("odoo_tax", "Odoo Default Tax Behaviour"), ("create_shopify_tax",
                                                      "Create new tax If Not Found")],
        copy=False, help=""" For Shopify Orders :- \n
                    1) Odoo Default Tax Behaviour - The Taxes will be set based on Odoo's
                                 default functional behaviour i.e. based on Odoo's Tax and Fiscal Position configurations. \n
                    2) Create New Tax If Not Found - System will search the tax data received 
                    from Shopify in Odoo, will create a new one if it fails in finding it.""")
    invoice_tax_account_id = fields.Many2one('account.account', string='Invoice Tax Account')
    credit_tax_account_id = fields.Many2one('account.account', string='Credit Tax Account')
    shopify_warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse',
                                           help="Selected Warehouse will be set in your Shopify "
                                                "orders.", required=False)
    domain_name = fields.Char(string='Domain', required=True, help="Example: example.com")
    gift_card_product_id = fields.Many2one("product.product", domain=[('type', '=', 'service')])

    
    def get_session(self):
        shopify.Session.setup(api_key=self.api_key, secret=self.api_secret)
        session = shopify.Session(self.shop_url, '2024-07', self.access_token)
        return session
    
    
    def action_sync_products(self):
        self.last_sync_date = datetime.now()
        self._sync_products_in_background()
        return True
    
    def _sync_products_in_background(self):
        self.env['shopify.sync'].sync_products(self.get_session())
        
    def sync_data(self):
        _logger.info("Synchronization started for record: %s", self.name)
        # Your synchronization logic here
        _logger.info("Synchronization completed for record: %s", self.name)

    def action_sync_products_(self):
        self.sync_data()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
        
    def shopify_test_connection(self, vals={}):
        self.connect_in_shopify(vals)
        try:
            shop_id = shopify.Shop.current()
        except ForbiddenAccess as e:
            if e.response.body:
                errors = json.loads(e.response.body.decode())
                raise UserError("%s\n%s\n%s" % (e.response.code, e.response.msg, errors.get("errors")))
        except Exception as e:
            raise UserError(e)
        shop_detail = shop_id.to_dict()
        self.write({"shopify_store_time_zone": shop_detail.get("iana_timezone")})
        title = _("Shopify")
        message = _("Connection Test Succeeded!")
        self.env['bus.bus']._sendone(
            (self._cr.dbname, 'res.partner', self.env.user.partner_id.id),
            'notification_type',  # Remplacez par le type de notification approprié
            {'message': message}
        )

        return True
    
    def connect_in_shopify(self, vals={}):
        session = self.get_session()
        shopify.ShopifyResource.activate_session(session)
        return True
    
    @api.model
    def _default_shipping_product(self):
        shipping_product = self.env.ref('market_connector.shopify_shipping_product') or False
        return shipping_product

    def generate_shopify_product_qr_codes(self):
        product_data_queue = self.env['merket.connector.products.data.queue']
        
        product_records = product_data_queue.search([
            ('product_id', '!=', False)
        ])
        
        if not product_records:
            _logger.info(f"No product records found for Shopify instance: {self.name}")
            return False
        
        try:
            for record in product_records:
                if not record.data:
                    continue
                
                try:
                    data_dict = json.loads(record.data)
                    
                    shop_url = self._extract_shop_url(data_dict.get('vendor',''))
                    
                    product_handle = data_dict.get('handle')
                    
                    if not product_handle:
                        continue
                    
                    shop_url = shop_url.rstrip('/')
                    product_url = f"{shop_url}/products/{product_handle}"
                    
                    qr = qrcode.QRCode(
                        version=1, 
                        box_size=10, 
                        border=5
                    )
                    qr.add_data(product_url)
                    qr.make(fit=True)
                    
                    qr_image = qr.make_image(fill_color="black", back_color="white")
                    
                    buffer = io.BytesIO()
                    qr_image.save(buffer, format="PNG")
                    
                    qr_code_base64 = base64.b64encode(buffer.getvalue())
                    
                    if record.product_id:
                        record.product_id.write({
                            'qr_code_uploaded': qr_code_base64
                        })
                    
                    _logger.info(f"Generated QR Code for product: {product_url}")
                
                except Exception as e:
                    _logger.error(f"Error generating QR code for record {record.id}: {str(e)}")
            
            return True
        
        except Exception as main_error:
            _logger.error(f"Error in generating QR codes for Shopify instance {self.name}: {str(main_error)}")
            return False

    def action_generate_product_qr_codes(self):
        self.generate_shopify_product_qr_codes()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def _extract_shop_url(self, vendor):
        vendor = vendor.lower().replace(' ', '')
        
        if vendor == 'designertrim':
            return 'https://designertrim.com'
        
        return 'https://retailer.luxwoodtrim.com'
