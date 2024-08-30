import logging
import json
import time
from ..libs.pyactiveresource.connection import ClientError
from odoo import models, fields, api
from dateutil import parser
from datetime import datetime
from ..libs import shopify

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
        return self.matching_product_product(shopify_product)
    
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
                self.product_id = products[0]
                products[0].shopify_id = self.shopify_id
                result += "Done"
            elif len(products) == 0:
                result += "Not Found"
            else:
                result += "Conflict"

        self.result = result

    
    def matching_product_product(self, shopify_product):
        _logger.info(f"Strat Matching Product{shopify_product}")
        by_modele = True
        by_style = False
        by_brand = True
        referance = shopify_product.shopify_reference
        referance = referance.strip()
        # if referance.startswith("#"):
        #     referance = referance[1:]
        domain = [("name", "=", referance)]
        if by_modele:
            domain.append(("product_template_variant_value_ids.name", "=", shopify_product.model))
        if by_style:
            domain.append(("product_template_variant_value_ids.name", "=", shopify_product.style)) # shopify_product.style
        if by_brand:
            domain.append(("product_template_variant_value_ids.name", "=", shopify_product.brand))
            
        product = self.env['product.product'].search(domain)
        product_count = len(product)
        _logger.info(f"List of products found : {product} | count {product_count}")
        if product_count == 1:
            shopify_product.product_id = product
            product.shopify_id = shopify_product.shopify_id
        elif product_count == 0:
            # TODO :  Problème matching 
            _logger.info("No Product Matching")
            _logger.info(f"""
                          Product Referance: {referance} \n
                          Model : {shopify_product.model} \n 
                          Brand : {shopify_product.brand} \n 
                          Search domain : {domain}
                          """)
            product = self.env['product.product'].search([("name", "=", "default product")])
            shopify_product.product_id = product
            product.shopify_id = shopify_product.shopify_id
        else:
            _logger.info("Conflict")
            product  = product[0]
            shopify_product.product_id = product
            product.shopify_id = shopify_product.shopify_id
        _logger.info(f"product : {product}")
        return product
    
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
        
