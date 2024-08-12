
class ShopifyProductDataQueueEpt(models.Model):
    _name = "merket.connector.templates.data.queue"
    _inherit = ["mail.thread", "mail.activity.mixin"]


    def shopify_sync_products(self, product_data_line_id, shopify_tmpl_id, instance, log_book_id,
                                order_data_line_id=False):
            """
            This method is used to sync products from queue line or shopify template id for Order.
            @param product_data_line_id: Product Queue Line.
            @param shopify_tmpl_id: Id of shopify template, to import particular product, when not found while processing
            the order.
            @param instance: Shopify Instance.
            @param log_book_id: Common Log Book.
            @param order_data_line_id: Order Queue Line, when needed to import a product for a order.
            @author: Maulik Barad on Date 01-Sep-2020.
            """
            common_log_line_obj = self.env["common.log.lines.ept"]

            model_id = common_log_line_obj.get_model_id("shopify.product.template.ept")
            instance.connect_in_shopify()

            template_data, skip_existing_product = self.convert_shopify_template_response(shopify_tmpl_id,
                                                                                        product_data_line_id, model_id,
                                                                                        log_book_id, order_data_line_id)

            if not template_data:
                return True

            _logger.info("Process started for Product- %s || %s.", template_data.get("id"), template_data.get("title"))

            product_category = self.get_product_category(template_data.get("product_type"))

            shopify_template = self.search(
                [("shopify_tmpl_id", "=", template_data.get("id")),
                ("shopify_instance_id", "=", instance.id)])

            if shopify_template:
                self.sync_product_with_existing_template(shopify_template, skip_existing_product, template_data, instance,
                                                        product_category, model_id, log_book_id, product_data_line_id,
                                                        order_data_line_id)
                if not skip_existing_product and instance.sync_product_with_images and shopify_tmpl_id:
                    shopify_template.shopify_sync_product_images(template_data)
            else:
                shopify_template = self.sync_new_product(template_data, instance, product_category, model_id, log_book_id,
                                                        product_data_line_id, order_data_line_id)
                if shopify_template and instance.sync_product_with_images and shopify_tmpl_id:
                    shopify_template.shopify_sync_product_images(template_data)

            if shopify_template and product_data_line_id:
                product_data_line_id.write({"state": "done", "last_process_date": datetime.now()})

            _logger.info("Process completed of Product- %s || %s.", template_data.get("id"), template_data.get("title"))

            return shopify_template