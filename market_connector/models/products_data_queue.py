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
            print(reference[-3:])
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
            
    
    def check_matching(self):
        produc_product = self.env['product.product']
        products = produc_product.search([("name", "=", self.shopify_reference)])
        result = f'check ref : {len(products)}\n'

        if len(products) > 0:
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
                    if not self.default_image_url and self.data :
                        result +=f"==> No Image \n"
                        data_dict = json.loads(self.data)
                        self.default_image_url = data_dict.get('image',{'src':None}).get('src')
                        self.add_images_from_dict(products[0],data_dict.get('images',[]))
                        result +=f"==> Url : {self.default_image_url} \n"
                    check_image = self.import_shopify_product_image(products[0], self.default_image_url)
                    if self.default_image_url:
                        return False
                    result +=f"Sync Image : {check_image}\n"
                    result += "Done"
                else:
                    result += "No matching Brand or Model"
            elif len(products) == 0:
                result += "Not Found"
            else:
                result += "Conflict"

        self.result = result

    
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
            if shopify_product.style:
                attributes.append(shopify_product.style)
            
            product_name = f"{reference} ({','.join(attributes) if attributes else ''})"

            # Créer le produit
            product = self.env['product.product'].create({
                    'name': product_name,
                    'default_code': reference,
                    'type': 'product',
                    'categ_id': category.id if category else False,
                })
            
            # Affecter tous les attributs existants
            self._set_all_product_attributes(product)
            
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
    
    def _set_all_product_attributes(self, product):
        ProductTemplateAttributeLine = self.env['product.template.attribute.line']
        
        # Récupérer tous les attributs
        attributes = self.env['product.attribute'].search([
            ('name', 'in', ['MAIN COLOR', 'CARBON CODE', 'Année'])
        ])
        
        for attribute in attributes:
            # Récupérer toutes les valeurs pour cet attribut
            values = self.env['product.attribute.value'].search([
                ('attribute_id', '=', attribute.id)
            ])
            
            if values:
                # Créer la ligne d'attribut sur le template du produit avec toutes les valeurs
                ProductTemplateAttributeLine.create({
                    'product_tmpl_id': product.product_tmpl_id.id,
                    'attribute_id': attribute.id,
                    'value_ids': [(6, 0, values.ids)]
                })
    
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
    

    
        
