import logging
import re
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class WhatsAppMessage(models.Model):
    _inherit = 'whatsapp.message'  

    @api.model
    def create(self, vals):
       
        record = super(WhatsAppMessage, self).create(vals)
        
        # Process the message to create an order, if applicable
        record.process_whatsapp_message(record)

        return record

    def process_whatsapp_message(self, message):
        # Required keys for order creation
        required_keys = ["Représentant","Référence","Marque", "Modele", "Année", "Style", "Color", "Destination"]

        # Clean the message body to remove HTML tags
        clean_message_body = self.clean_html_tags(message.body)

        # Log cleaned message body for debugging
        _logger.info("Cleaned message body: %s", clean_message_body)

        # Extract key-value pairs from the cleaned message
        message_data = self.extract_key_value_pairs(clean_message_body)

        # Check if all required fields are present
        if all(key in message_data for key in required_keys):
            # Create sale order based on the parsed data
            self.create_order_from_whatsapp_data(message_data, message.mobile_number)
        else:
            # Log the issue if the structure is incorrect
            _logger.error("The message does not contain all the required information for an order: %s", clean_message_body)

    def clean_html_tags(self, text):
        """Remove HTML tags from the message body"""
        clean_text = re.sub(r'<.*?>', '', text)  # Regex to remove HTML tags
        return clean_text

    def extract_key_value_pairs(self, text):
        message_data = {}
    
        # Define regex patterns for each label
        patterns = {
            'Représentant': re.compile(r'Représentant\s*:\s*([^\n]+?)(?=\s*Référence\s*:|$)', re.IGNORECASE),
            'Référence': re.compile(r'Référence\s*:\s*([^\n]+?)(?=\s*Marque\s*:|$)', re.IGNORECASE),
            'Marque': re.compile(r'Marque\s*:\s*([^\n]+?)(?=\s*Modele\s*:|$)', re.IGNORECASE),
            'Modele': re.compile(r'Modele\s*:\s*([^\n]+?)(?=\s*Année\s*:|$)', re.IGNORECASE),
            'Année': re.compile(r'Année\s*:\s*([^\n]+?)(?=\s*Style\s*:|$)', re.IGNORECASE),
            'Style': re.compile(r'Style\s*:\s*([^\n]+?)(?=\s*Color\s*:|$)', re.IGNORECASE),
            'Color': re.compile(r'Color\s*:\s*([^\n]+?)(?=\s*Destination\s*:|$)', re.IGNORECASE),
            'Destination': re.compile(r'Destination\s*:\s*([^\n]+)', re.IGNORECASE),
        }
    
        # Extract data for each label
        for key, pattern in patterns.items():
            match = pattern.search(text)
            if match:
                message_data[key] = match.group(1).strip()
                _logger.info("Matched %s: %s", key, message_data[key])
    
        # Log the parsed data for debugging
        _logger.info("Parsed message data: %s", message_data)
    
        # Check for missing required fields
        required_fields = ['Représentant','Référence', 'Marque', 'Modele', 'Année', 'Style', 'Color', 'Destination']
        missing_fields = [field for field in required_fields if field not in message_data]
    
        if missing_fields:
            _logger.error("Missing fields in the message: %s", missing_fields)
            return None  # or handle the error appropriately
    
        return message_data
    
    def create_order_from_whatsapp_data(self, message_data, mobile_number):
        
        # Lookup representative (client) based on their WhatsApp mobile number
        client_partner = self.env['res.partner'].search([('mobile', '=', mobile_number)], limit=1)

        if not client_partner:
            _logger.error("Representative (Client) with phone %s not found.", mobile_number)
            return  # Exit without creating an order

        # Extract data from the message
        brand = message_data.get('Marque')
        model = message_data.get('Modele')
        year = message_data.get('Année')
        style = message_data.get('Style')
        color = message_data.get('Color')
        destination = message_data.get('Destination')
        reference = message_data.get('Référence')
        

        # Search for a product that matches these attributes
        product = self.get_matching_product(reference,brand, model, year, style, color)

        if not product:
            _logger.error("No matching product found for reference:%s,  Brand: %s, Model: %s, Year: %s, Style: %s, Color: %s",reference, brand, model, year, style, color)
            return  # Exit without creating an order

        # Create the sale order
        sale_order = self.env['sale.order'].create({
            'partner_id': client_partner.id,  # The representative (client)
            'from_whatsapp':True,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': 1,  # Or dynamically set quantity
                'price_unit': product.list_price,  # Set price to product's list price
            })],
            'partner_shipping_id': self.get_destination_partner(destination).id  # The destination (delivery address)
        })
        return sale_order


    import logging

    def get_matching_product(self, reference, brand, model, year, style, color): 
       
        _logger = logging.getLogger(__name__)
        
        # Step 1: Search for the base product by reference
        product = self.env['product.product'].search([
            ('name', 'ilike', f'#{reference}')
        ], limit=1)
    
        if not product:
            raise ValueError(f"No product found with reference: {reference}")
        
        _logger.info(f"Product found: {product.name}")
    
        # Step 2: Search for the corresponding attributes by name
        attribute_marque = self.env['product.attribute'].search([('name', '=', 'Marques')], limit=1)
        attribute_modele = self.env['product.attribute'].search([('name', '=', 'Modèle')], limit=1) if model else None
        attribute_annee = self.env['product.attribute'].search([('name', '=', 'Année')], limit=1)
        attribute_style = self.env['product.attribute'].search([('name', '=', 'Style')], limit=1)
        attribute_color = self.env['product.attribute'].search([('name', '=', 'INSERT COLOR')], limit=1)
    
        # Step 3: Ensure necessary attributes are found
        if not all([attribute_marque, attribute_annee, attribute_style, attribute_color]):
            raise ValueError("One or more product attributes not found")
    
        # Step 4: Search for specific attribute values using the corresponding attribute
        marque_value = self.env['product.attribute.value'].search([('attribute_id', '=', attribute_marque.id), ('name', '=', brand)], limit=1)
        if not marque_value:
            raise ValueError("Brand not found")
        
        _logger.info(f"Brand attribute value found: {marque_value.name}")
    
        modele_value = None
        if model and attribute_modele:
            modele_value = self.env['product.attribute.value'].search([('attribute_id', '=', attribute_modele.id), ('name', '=', model)], limit=1)
            if not modele_value:
                raise ValueError("Model not found")
            _logger.info(f"Model attribute value found: {modele_value.name}")
    
        annee_value = self.env['product.attribute.value'].search([('attribute_id', '=', attribute_annee.id), ('name', '=', year)], limit=1)
        if not annee_value:
            raise ValueError("Year not found")
        _logger.info(f"Year attribute value found: {annee_value.name}")
    
        style_value = self.env['product.attribute.value'].search([('attribute_id', '=', attribute_style.id), ('name', '=', style)], limit=1)
        if not style_value:
            raise ValueError("Style not found")
        _logger.info(f"Style attribute value found: {style_value.name}")
    
        color_value = self.env['product.attribute.value'].search([('attribute_id', '=', attribute_color.id), ('name', '=', color)], limit=1)
        if not color_value:
            raise ValueError("Color not found")
        _logger.info(f"Color attribute value found: {color_value.name}")
    
        # Step 5: Build search domain for product variants
        attribute_value_ids = [marque_value.id, annee_value.id, style_value.id, color_value.id]
        if modele_value:
            attribute_value_ids.append(modele_value.id)
    
        _logger.info(f"Attribute value IDs for search: {attribute_value_ids}")
    
        # Step 6: Search for the matching product variant by template and attribute values
        product_variant = self.env['product.product'].search([
            ('product_tmpl_id', '=', product.product_tmpl_id.id),
            ('product_template_attribute_value_ids.product_attribute_value_id', 'in', attribute_value_ids)
        ])

        
    
        if product_variant:
             product_variant = product_variants[-1]
            _logger.info(f"Product variant found: {product_variant.name}")
            return product_variant
        else:
            raise ValueError(f"No matching variant found for reference: {reference}, Brand: {brand}, Model: {model}, Year: {year}, Style: {style}, Color: {color}")


    
    def get_destination_partner(self, destination_name):
        """Retrieve or create a partner for the destination"""
        destination_partner = self.env['res.partner'].search([('name', '=', destination_name)], limit=1)
        if not destination_partner:
            destination_partner = self.env['res.partner'].create({'name': destination_name})
        return destination_partner
