import logging
import re
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class WhatsAppMessage(models.Model):
    _inherit = 'whatsapp.message'  # Inheriting the existing model

    @api.model
    def create(self, vals):
     
        record = super(WhatsAppMessage, self).create(vals)
        
        record.process_whatsapp_message(record)

        return record

    def process_whatsapp_message(self, message):
        
        required_keys = ["Représentant", "Marque", "Modele", "Année", "Style", "Color", "Destination"]

        # Clean the message body to remove HTML tags
        clean_message_body = self.clean_html_tags(message.body)

        # Split cleaned message body by lines and filter out empty ones
        message_lines = [line.strip() for line in clean_message_body.split('\n') if line.strip()]

      
        message_data = {}

        # Parse each line
        for line in message_lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key, value = key.strip(), value.strip()
                if key in required_keys:
                    message_data[key] = value

      
        if all(key in message_data for key in required_keys):
           
            self.create_order_from_whatsapp_data(message_data, message.mobile_number)
        else:
            
            _logger.error("The message does not contain all the required information for an order: %s", clean_message_body)

    def clean_html_tags(self, text):
        """Remove HTML tags from the message body"""
        clean_text = re.sub(r'<.*?>', '', text)  # Regex to remove HTML tags
        return clean_text

    def create_order_from_whatsapp_data(self, message_data, mobile_number):
      
       
        client_partner = self.env['res.partner'].search([('phone', '=', mobile_number)], limit=1)

        if not client_partner:
            _logger.error("Representative (Client) with phone %s not found.", mobile_number)
            return  # Exit without creating an order

      
        brand = message_data.get('Marque')
        model = message_data.get('Modele')
        year = message_data.get('Année')
        style = message_data.get('Style')
        color = message_data.get('Color')
        destination = message_data.get('Destination')

        
        product = self.get_matching_product(brand, model, year, style, color)

        if not product:
            _logger.error("No matching product found for Brand: %s, Model: %s, Year: %s, Style: %s, Color: %s", brand, model, year, style, color)
            return  # Exit without creating an order

      
        sale_order = self.env['sale.order'].create({
            'partner_id': client_partner.id,  # The representative (client)
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': 1,  # Or dynamically set quantity
                'price_unit': product.list_price,  # Set price to product's list price
            })],
            'partner_shipping_id': self.get_destination_partner(destination).id  # The destination (delivery address)
        })
        return sale_order

    def get_matching_product(self, brand, model, year, style, color):
     
        product_tmpl = self.env['product.template'].search([
            ('attribute_line_ids.attribute_id.name', 'in', ['Marque', 'Modele', 'Année', 'Style', 'Color']),
            ('attribute_line_ids.value_ids.name', 'in', [brand, model, year, style, color])
        ], limit=1)

        if product_tmpl:
            # If product template is found, return the corresponding product variant (if applicable)
            product_variant = product_tmpl.product_variant_id
            return product_variant if product_variant else product_tmpl
        return None

    def get_destination_partner(self, destination_name):
       
        destination_partner = self.env['res.partner'].search([('name', '=', destination_name)], limit=1)
        if not destination_partner:
            destination_partner = self.env['res.partner'].create({'name': destination_name})
        return destination_partner
