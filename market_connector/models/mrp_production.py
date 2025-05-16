# -*- coding: utf-8 -*-

import base64
import qrcode
from io import BytesIO
from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    product_url = fields.Char(
        string="Product URL",
        help="URL to the product page",
        compute="_compute_product_url",
        store=True,
    )
    
    qr_code = fields.Binary(
        string="QR Code",
        compute="_compute_qr_code",
        store=True,
        help="QR code generated from the product URL"
    )
    
    @api.depends('product_url')
    def _compute_qr_code(self):
        for record in self:
            if record.product_url:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(record.product_url)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                record.qr_code = base64.b64encode(buffer.getvalue())
            else:
                record.qr_code = False 

    @api.depends('origin', 'product_id','shopify_instance_id')
    def _compute_product_url(self):
        for record in self:
            if record.product_id:  
                record.product_url = record.shopify_instance_id.shop_url + '/products/' + record.product_id.handle
            else:
                record.product_url = False