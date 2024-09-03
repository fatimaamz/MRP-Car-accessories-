from odoo import models, fields, api
from datetime import date
import logging



from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create(self, vals):
        order = super(SaleOrder, self).create(vals)
        order._add_global_discount_line()
        return order

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        for order in self:
            order._add_global_discount_line()
        return res

    def _add_global_discount_line(self):
        # Rechercher le produit de remise globale
        discount_product = self.env['product.product'].search([('name', '=', 'Remise')], limit=1)
        
        if not discount_product:
            return
        discount_amount = 0.0
        # Calcul du montant total avant remise
        total_amount = sum(line.price_subtotal for line in self.order_line)
        
        if self.partner_id.country_id.code == 'US':
            usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
            
            if usd_currency:
                today = date.today()
                
                # Chercher le taux du jour ou le plus récent
                rate_record = usd_currency.rate_ids.filtered(lambda r: r.name == today)
                if not rate_record:
                    rate_record = usd_currency.rate_ids.sorted(key=lambda r: r.name, reverse=True)[:1]
                
                # Si le taux est trouvé, convertir le total avant d'appliquer la remise
                if rate_record:
                    converted_total_amount = total_amount * rate_record.inverse_company_rate
                    discount_amount = - (converted_total_amount * 0.75)  # Appliquer la remise de 75%
              
            else:
                pass
       
            discount_line = self.order_line.filtered(lambda line: line.product_id == discount_product)
        
            if discount_line:
                discount_line.write({
                    'price_unit': discount_amount,
                    
                })
            else:
                # Ajouter une nouvelle ligne de remise
                self.order_line.create({
                    'order_id': self.id,
                    'name':'Remise: 75%',
                    'product_id': discount_product.id,
                    'price_unit': discount_amount,
                    'product_uom_qty': 1,
                })
        else:
            pass
