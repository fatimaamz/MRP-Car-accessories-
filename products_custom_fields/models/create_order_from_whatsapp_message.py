from odoo import models, fields, api
from odoo.exceptions import ValidationError

class WhatsAppMessage(models.Model):
    _inherit = 'whatsapp.message'  # Inheriting the existing model

    @api.model
    def create(self, vals):
        # Create the record first
        record = super(WhatsAppMessage, self).create(vals)
        
        # Process the message to create an order, if applicable
        record.process_whatsapp_message(record)

        return record

    def process_whatsapp_message(self, message):
        # Sample structure of the message
        required_keys = ["Représentant", "Marque", "Modele", "Année", "Style", "Color", "Destination"]

        # Split message body by lines and filter out empty ones
        message_lines = [line.strip() for line in message.body.split('\n') if line.strip()]

        # Create a dictionary to store parsed information
        message_data = {}

        # Parse each line
        for line in message_lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key, value = key.strip(), value.strip()
                if key in required_keys:
                    message_data[key] = value

        # Check if all required fields are present
        if all(key in message_data for key in required_keys):
            # Create sale order based on the parsed data
            self.create_order_from_whatsapp_data(message_data, message.from_number)
        else:
            # If the structure is incorrect, raise an exception or log the issue
            raise ValidationError("The message does not contain all the required information for an order.")

    def create_order_from_whatsapp_data(self, message_data, representative_number):
        """Creates a sale order from the parsed WhatsApp data"""
        # Lookup representative based on their WhatsApp number
        rep_partner = self.env['res.partner'].search([('phone', '=', representative_number)], limit=1)

        if not rep_partner:
            raise ValidationError(f"Representative with phone {representative_number} not found.")

        # Extract data from the message
        brand = message_data.get('Marque')
        model = message_data.get('Modele')
        year = message_data.get('Année')
        style = message_data.get('Style')
        color = message_data.get('Color')
        destination = message_data.get('Destination')

        # Search for a product that matches these attributes
        product = self.get_matching_product(brand, model, year, style, color)

        if not product:
            raise ValidationError(f"No matching product found for Brand: {brand}, Model: {model}, Year: {year}, Style: {style}, Color: {color}")

        # Create the sale order
        sale_order = self.env['sale.order'].create({
            'partner_id': rep_partner.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': 1,  # Or dynamically set quantity
                'price_unit': product.list_price,  # Set price to product's list price
            })],
            'partner_shipping_id': self.get_destination_partner(destination).id
        })
        return sale_order

    def get_matching_product(self, brand, model, year, style, color):
        """Retrieve a product that matches the specified attributes"""
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
        """Retrieve or create a partner for the destination"""
        destination_partner = self.env['res.partner'].search([('name', '=', destination_name)], limit=1)
        if not destination_partner:
            destination_partner = self.env['res.partner'].create({'name': destination_name})
        return destination_partner
