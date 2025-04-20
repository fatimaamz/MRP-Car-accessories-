import logging
import json
import time
from ..libs.pyactiveresource.connection import ClientError
import ast
from odoo import models, fields, api
from dateutil import parser
from datetime import datetime
from ..libs import shopify
import base64
import requests
from odoo.exceptions import UserError

_logger = logging.getLogger("Shopify Order")

class ShopifyProductDataQueueEpt(models.Model):
    _name = "merket.connector.products.data.queue"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    
    name = fields.Char(size=120) 
    is_process_queue = fields.Boolean("Is Processing Queue", default=False)
    shopify_id = fields.Char()
    shopify_title = fields.Char()
    shopify_name = fields.Char()
    brand = fields.Char()
    style = fields.Char()
    model = fields.Char()
    shopify_years = fields.Char()
    shopify_attribute = fields.Char()
    shopify_reference = fields.Char()
    variant_id = fields.Char()
    default_image_url = fields.Char()
    data = fields.Char()
    product_id = fields.Many2one('product.product', string="Product", required=False)
    shopify_instance_id = fields.Many2one("shopify.credentials", "Compte", copy=False)
    is_match_name = fields.Boolean("Is Match Name", default=False)
    is_match_brand = fields.Boolean("Is Match Brand", default=False)
    is_match_style = fields.Boolean("Is Match Style", default=False)
    is_match_model = fields.Boolean("Is Match Model", default=False)
    result = fields.Char()
    
    
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
            brands = [
                "GMC", "JEEP", "Ford", "RAM", "Chevrolet", "JEEP", "Kia", "MITSUBISHI",
                "Toyota", "Acura", "Alfa Romeo", "Audi", "BMW", "Cadillac", "Campagna",
                "Chrysler", "Dodge", "Genesis", "Honda", "Infiniti", "Hyundai", "Jeep",
                "Land Rover", "Lexus", "Lincoln", "Mack", "Maserati", "Mazda", "Mercedes-Benz",
                "Mitsubishi", "Nissan", "Peterbilt", "Ram", "Scion", "Subaru", "Volkswagen",
                "Volvo", "Tesla", "Buick", "Fiat", "Universal", "International", "Jaguar",
                "Kenworth", "Porsche"
            ]
            brand =  next((b for b in brands if name.startswith(b)), None)
            model = name[len(brand):].strip()
            years = split_title[1]
            attribute = split_title[2]
            reference = split_title[3]
            result = result.to_dict()
            data = json.dumps(result)
            product = self.create({
                    'shopify_id': result.get('id'),
                    'shopify_title': result.get('title'),
                    'default_image_url' : result.get('image',{'src':None}).get('src'),
                    'shopify_name': name,
                    'shopify_years': years,
                    'brand': brand,
                    'model': model,
                    'style': reference[-3:],
                    'shopify_attribute': attribute,
                    'shopify_reference': reference,
                    'data' : data
                })
            self._cr.commit()
            return product
        except IndexError:
            print(split_title)
        except Exception as err:
            print(err)
            
    def shopify_sync_products(self,shopify_id, instance):
        shopify_product = self.search([("shopify_id", "=", shopify_id)],limit=1)
        if not shopify_product:
            # TODO : Fix le problème return None
            shopify_product =  self.new_signle_product(shopify_id, instance)
        product_product =  self.matching_product_product(shopify_product)
        
        return product_product
    
    def matching_products(self):
        for record in self:
            print(record)
            self.macthing_product(record)
            
            
    def check_matching_action(self):
        for record in self:
            record.check_matching()
            self._cr.commit()

    def process_check_matching_in_batch(self):
        """Process check matching for multiple records"""
        for record in self:
            try:
                record.check_matching()
                self._cr.commit()

            except Exception as e:
                _logger.error(f"Error processing record {record.name}: {str(e)}")
                self._cr.commit()


    
            
    
    def check_matching(self):
        produc_product = self.env['product.product']
        # Search only by default_code and exclude archived products
        products = produc_product.search([
            ("default_code", "=", self.shopify_reference),
            ("active", "=", True)
        ])
        result = f'check ref : {len(products)}\n'

        if len(products) == 0:
            # Use existing matching_product_product method if no product found
            try:
                product = self.matching_product_product(self)
                result += "New product created successfully"
            except Exception as e:
                result += f"Error creating product: {str(e)}"
        else:
            # Existing matching logic for found products
            self.is_match_name = True
            products_model = products.filtered(lambda p: self.model in p.product_template_variant_value_ids.mapped('name'))
            result += f'Model : {len(products_model)}/{len(products)} \n'
            if len(products_model) > 0:
                self.is_match_model = True
                products = products_model

            products_brand = products.filtered(lambda p: self.brand in p.product_template_variant_value_ids.mapped('name'))
            result += f'Brand : {len(products_brand)}/{len(products)}\n'
            if len(products_brand) > 0:
                self.is_match_brand = True
                products = products_brand

            products_style = products.filtered(lambda p: self.style in p.product_template_variant_value_ids.mapped('name'))
            result += f'Style : {len(products_style)}/{len(products)}\n'
            if len(products_style) > 0:
                self.is_match_style = True
                products = products_style
            if len(products) == 1:
                if self.is_match_brand and self.is_match_model:
                    self.product_id = products[0]
                    products[0].shopify_id = self.shopify_id
                    if not self.default_image_url and self.data:
                        result += f"==> No Image \n"
                        data_dict = json.loads(self.data)
                        self.default_image_url = data_dict.get('image', {'src': None}).get('src')
                        self.add_images_from_dict(products[0], data_dict.get('images', []))
                        result += f"==> Url : {self.default_image_url} \n"
                    check_image = self.import_shopify_product_image(products[0], self.default_image_url)
                    if self.default_image_url:
                        return False
                    result += f"Sync Image : {check_image}\n"
                    result += "Done"
                else:
                    result += "No matching Brand or Model"
            else:
                result += "Conflict"

        self.result = result
        
    def create_or_update(self):
        for record in self:
            _logger.info(f"Processing product: {record.shopify_reference}")
            reference = record.shopify_reference.strip()
            
            # Get product data from Shopify
            data_dict = {}
            if record.data:
                data_dict = json.loads(record.data)
            
            # Get or create category from product_type
            category = False
            product_type = data_dict.get('product_type')
            if product_type:
                category = self.env['product.category'].search([('name', '=', product_type)], limit=1)
                if not category:
                    category = self.env['product.category'].create({'name': product_type})
            
            # Search for existing product template by default_code
            product_tmpl = self.env['product.template'].search([
                ('default_code', '=', reference),
                ('active', '=', True)
            ], limit=1)

            # Prepare attribute values for name
            attr_for_name = []
            if record.model:
                attr_for_name.append(record.model)
                
            if record.brand:
                attr_for_name.append(record.brand)
            if record.shopify_attribute:
                attr_for_name.append(record.shopify_attribute)
                
            product_name = f"{reference} ({','.join(attr_for_name) if attr_for_name else ''})"

            attributes = self.get_attributes(record)

            print(attributes)
            
            if not product_tmpl:
                _logger.info(f"No product template found for reference: {reference}, creating new one")
                
                
                
                # Create new product template
                product_tmpl = self.env['product.template'].create({
                    'name': product_name,
                    'default_code': reference,
                    'type': 'product',
                    'categ_id': category.id if category else False,
                    'shopify_id': record.shopify_id
                })
                
                # Apply attributes
                self.apply_record_attributes(product_tmpl, record)
                
                # Create variant if needed
                product_product = product_tmpl.product_variant_id
                
                # Import images
                if record.default_image_url:
                    self.import_shopify_product_image(product_product, record.default_image_url)
                
                # Add additional images
                self.add_images_from_dict(product_product, data_dict.get('images', []))
                
                # Link the product to the queue record
                record.product_id = product_product.id
                
                _logger.info(f"Created new product: {product_tmpl.name}")
                return product_product
            else:
                _logger.info(f"Product template found: {product_tmpl.name}, updating")
                
                # Update existing product
                product_product = product_tmpl.product_variant_id
                product_tmpl.shopify_id = record.shopify_id
                
                # Update category if needed
                if category:
                    product_tmpl.categ_id = category.id
                
                # Apply all attributes
                self.apply_record_attributes(product_tmpl, record)
                
                # Update images if needed
                if record.default_image_url and not product_product.image_1920:
                    self.import_shopify_product_image(product_product, record.default_image_url)
                
                # TODO : Add additional images if needed
                # Add additional images if needed
                # if not self.env['product.image'].search([('product_tmpl_id', '=', product_tmpl.id)]):
                #     self.add_images_from_dict(product_product, data_dict.get('images', []))
                
                # Link the product to the queue record
                record.product_id = product_product.id
                
                _logger.info(f"Updated product: {product_tmpl.name}")
            self._cr.commit()

    
    def matching_product_product(self, shopify_product):
        _logger.info(f"Start Matching Product{shopify_product}")
        by_modele = True
        by_style = False
        by_brand = True
        reference = shopify_product.shopify_reference.strip()
        
        # Get or create category from Shopify product_type
        data_dict = json.loads(shopify_product.data)
        product_type = data_dict.get('product_type')
        category = False
        if product_type:
            category = self.env['product.category'].search([('name', '=', product_type)], limit=1)
            if not category:
                category = self.env['product.category'].create({'name': product_type})
        
        # Search by default_code first and exclude archived products
        domain = [
            ("default_code", "=", reference),
            ("active", "=", True)  # Only consider active (non-archived) products
        ]
        if by_modele:
            domain.append(("product_template_variant_value_ids.name", "=", shopify_product.model))
        if by_style:
            domain.append(("product_template_variant_value_ids.name", "=", shopify_product.style))
        if by_brand:
            domain.append(("product_template_variant_value_ids.name", "=", shopify_product.brand))
            
        product = self.env['product.product'].search(domain)
        product_count = len(product)
        _logger.info(f"List of products found : {product} | count {product_count}")
        
        if product_count == 1:
            shopify_product.product_id = product
            product.shopify_id = shopify_product.shopify_id
            if category:
                product.categ_id = category.id
        elif product_count == 0:
            _logger.info("No Product Matching")
            _logger.info(f"""
                          Product Reference: {reference} \n
                          Model : {shopify_product.model} \n 
                          Brand : {shopify_product.brand} \n 
                          Search domain : {domain}
                          """)
            attributes = []
            if shopify_product.model:
                attributes.append(shopify_product.model)
            if shopify_product.brand:
                attributes.append(shopify_product.brand)
            if shopify_product.shopify_attribute:
                attributes.append(shopify_product.shopify_attribute)
            
            product_name = f"{reference} ({','.join(attributes) if attributes else ''})"

            # Créer le produit
            product = self.env['product.product'].create({
                    'name': product_name,
                    'default_code': reference,
                    'type': 'product',
                    'categ_id': category.id if category else False,
                })
            

            
            # Apply attributes
            self.apply_record_attributes(product.product_tmpl_id, shopify_product)
            
            shopify_product.product_id = product
            product.shopify_id = shopify_product.shopify_id
            if category:
                product.categ_id = category.id
        else:
            _logger.info("Conflict")
            product = product[0]
            shopify_product.product_id = product
            product.shopify_id = shopify_product.shopify_id
            if category:
                product.categ_id = category.id
        
        _logger.info(f"product : {product}")
        self.import_shopify_product_image(product, shopify_product.default_image_url)
        data_dict = json.loads(shopify_product.data)
        self.add_images_from_dict(product, data_dict.get('images',[]))
        return product
    
    @staticmethod
    def get_product_colors(tags):
        default_exterior_color = [
            "Glossy Black (0BK)", "Chrome (0CH)", "Luxd Carbon (LCF)", "Racing Red (RED)",
            "Orange tech (ORA)", "Paint match (0CM)", "Platinum Silver (0PS)", "Textured Carbon (WCF)",
            "Hot Pink (BCF)", "Electric Blue (0EB)", "Brushed Chrome (0BC)", "Titanium (PWT)",
            "African Rose (0AR)", "Cafe Burl (0CB)", "Maple Burl (0TK)", "Oxford Burl (OXB)", 
            "Royal Cherry (0RB)", "Black Rose (0BR)"
        ]

        default_insert_colors = [
            "No insert", "Chrome (0CH)", "Glossy Black (0BK)", "Luxd Carbon (LCF)", 
            "Racing Red (RED)", "Orange Tech (ORA)", "Paint Match (0CM)", 
            "Platinum Silver (0PS)", "Hot Pink (BCF)", "Electric Blue (0EB)"
        ]

        default_carbon_colors = [
            "Black Carbon Fiber - Twill (RCF)", "Honeycomb Carbon (HCF)", 
            "Metalic Red Carbon (MRF)", "Metalic Blue Carbon (MBF)", "Silver Carbon (CFS)"
        ]

        default_bpm_colors = ["Black Protection (WBK)", "Wrap Carbon (WCF)"]

        result = {}

        exterior_tags_1 = {"CRM", "CRP", "MTR", "RDS", "SMC", "SMP", "XCC", "XSC", "XRI", "XCI", "XSM", "XSP", "XSR", "CRK", "CRP"}
        
        exterior_tags_2 = {"DEK", "EXT", "GRI", "GRK", "GRL", "GRV", "PIK", "PIL", "RDL", "RKI", "RKK", "RKR", "BUL", "DEL", "BUM", "DEF"}
        
        exterior_tags_3 = {"LOG", "ACC", "WT", "WTT", "CRX"}
        
        interior_tags = {"CMB", "FAC", "FUL", "OEM", "RDL", "SET", "SGN"}
        

        bpm_tags = {"BPM"}
        if any(tag.strip() in exterior_tags_1 for tag in tags):
            result["MAIN COLOR"] = default_exterior_color
            result["INSERT COLOR"] = default_insert_colors
            result["CARBON COLOR"] = default_carbon_colors

        elif any(tag.strip() in exterior_tags_2 for tag in tags):
            result["MAIN COLOR"] = default_exterior_color
            result["INSERT COLOR"] = default_insert_colors
            result["CARBON COLOR"] = default_carbon_colors


        elif any(tag.strip() in interior_tags for tag in tags):
            pass
        elif any(tag.strip() in exterior_tags_3 for tag in tags):
            result["MAIN COLOR"] = default_exterior_color

        if any(tag.strip() in bpm_tags for tag in tags):
            if not result:
                result = {}
            result["PROTECTION FILM COLORS"] = default_bpm_colors

        return result


    
    def matching_product_template(self, shopify_product):
        product_template = self.env['product.template'].search([("name","=",shopify_product.shopify_reference)])
        if len(product_template) == 1:
            return product_template[0]
        elif len(product_template) == 0 :
            print("No Exist ... sync_product from shopify")
        else:
            return product_template[0]
        
        
    
    def new_signle_product(self,shopify_id, instance):
        instance.connect_in_shopify()
        shopify_product = self.env['shopify.sync'].process_single_product(shopify_id)
        _logger.info(f"New product {shopify_product}")
        return shopify_product
    
    
    def add_images_from_dict(self,product_product, images):
        print("========================================================>",images)
        for image_info in images:
            response = requests.get(image_info['src'])
            if response.status_code == 200:
                image_base64 = base64.b64encode(response.content)
                self.env['product.image'].create({
                    'product_id': product_product.id,
                    'image': image_base64,
                    'name': image_info.get('alt', ''),
                    'is_default': image_info.get('position', 0) == 1 
                })
    
    
    def import_shopify_product_image(self, product_product, image_url):
        if not image_url:
            _logger.info(f"No image URL found for Shopify Product ID: {product_product}")
            return False

        # Download the image
        try:
            response = requests.get(image_url)
            response.raise_for_status()  # Ensure we got the image
        except requests.exceptions.RequestException as e:
            raise UserError(f"Error downloading image from Shopify: {e}")

        # Convert the image to base64 to store in Odoo
        image_base64 = base64.b64encode(response.content)

        # Get the Odoo product template
        if not product_product:
            raise UserError(f"No product found with Shopify reference {product_product}")

        # Update the product template with the image
        product_product.write({
            'image_1920': image_base64  # Use the appropriate field for the image size
        })

        _logger.info(f"Successfully imported image for product: {product_product}")
        return True
    
    def force_sync(self):
        for record in self:
            self.matching_product_product(record)
            
            
    def create_order_data_queue_line(self, orders_data, instance, created_by="import"):
        count = 0
        need_to_create_queue = True
        orders_data.reverse()
        order_queue_list = []

        for order in orders_data:
            if created_by == "webhook":
                order_queue, need_to_create_queue = self.search_webhook_order_queue(created_by, instance, order,
                                                                                    need_to_create_queue)
            else:
                order = order.to_dict()

            if need_to_create_queue:
                order_queue = self.shopify_create_order_queue(instance, created_by)
                order_queue_list.append(order_queue.id)
                message = "Order Queue %s created." % order_queue.name
                # self.generate_simple_notification(message)
                self._cr.commit()
                need_to_create_queue = False
                _logger.info(message)

            data = json.dumps(order)
            customer_name, customer_email = self.get_customer_name_and_email(order)
            self.create_order_queue_line(order, instance, data, customer_name, customer_email, order_queue)
            if created_by == "webhook" and len(order_queue.order_data_queue_line_ids) >= 50:
                order_queue.order_data_queue_line_ids.process_import_order_queue_data(update_order=True)

            count += 1
            if count == 50:
                count = 0
                need_to_create_queue = True
        if not order_queue.order_data_queue_line_ids:
            order_queue.unlink()
            order_queue_list.remove(order_queue.id)

        return order_queue_list


    def get_attributes(self, record):
        attributes = []
        
        # Only add attributes that have values
        # if hasattr(record, 'model') and record.model:
        #     attributes.append({
        #         'name': 'Model',
        #         'value': record.model
        #     })
            
        # if hasattr(record, 'brand') and record.brand:
        #     attributes.append({
        #         'name': 'Brand',
        #         'value': record.brand
        #     })
            
        # if hasattr(record, 'style') and record.style:
        #     attributes.append({
        #         'name': 'Style',
        #         'value': record.style
        #     })
            
        if hasattr(record, 'shopify_years') and record.shopify_years:
            years_str = record.shopify_years.strip()
            if "-" in years_str:
                start_year, end_year = years_str.split("-")
                start_year = int(start_year.strip())
                end_year = int(end_year.strip())
                years = [str(year) for year in range(start_year, end_year + 1)]
            else:
                years = [years_str]
            attributes.append({
                'name': 'Année',
                'value': years
            })

        if hasattr(record, 'data') and record.data:
            data_dict = json.loads(record.data)
            tags_str = data_dict.get('tags', [])
            tags = tags_str.split(",")
            colors_attributes = self.get_product_colors(tags)
            colors_attributes = [{"name": key, "value": value} for key, value in colors_attributes.items()]
            attributes.extend(colors_attributes)
        return attributes
    

    def apply_attributes(self, product_template, attributes):
        attribute_obj = self.env['product.attribute']
        attribute_value_obj = self.env['product.attribute.value']
        attribute_line_obj = self.env['product.template.attribute.line']
        
        for attr in attributes:
            attr_name = attr.get('name')
            attr_value = attr.get('value')
            
            if not attr_name or not attr_value:
                continue
                
            # Find or create product attribute
            attribute = attribute_obj.search([('name', '=', attr_name)], limit=1)
            if not attribute:
                attribute = attribute_obj.create({'name': attr_name, 'create_variant': 'no_variant'})
                
            # Handle both single value and list of values
            values = attr_value if isinstance(attr_value, list) else [attr_value]
            
            # Find or create attribute values
            attr_values = []
            for value in values:
                if not value:
                    continue
                    
                attr_value_record = attribute_value_obj.search([
                    ('name', '=', value),
                    ('attribute_id', '=', attribute.id)
                ], limit=1)
                
                if not attr_value_record:
                    attr_value_record = attribute_value_obj.create({
                        'name': value,
                        'attribute_id': attribute.id
                    })
                
                attr_values.append(attr_value_record.id)
            
            if not attr_values:
                continue
                
            # Find or create attribute line
            attr_line = attribute_line_obj.search([
                ('product_tmpl_id', '=', product_template.id),
                ('attribute_id', '=', attribute.id)
            ], limit=1)
            
            if attr_line:
                # Update existing attribute line
                existing_values = attr_line.value_ids.ids
                new_values = list(set(existing_values + attr_values))
                attr_line.write({'value_ids': [(6, 0, new_values)]})
            else:
                # Create new attribute line
                attribute_line_obj.create({
                    'product_tmpl_id': product_template.id,
                    'attribute_id': attribute.id,
                    'value_ids': [(6, 0, attr_values)]
                })
        
        

    def apply_record_attributes(self, product_template, record):
        attributes = self.get_attributes(record)
        self.apply_attributes(product_template, attributes)
        
        
