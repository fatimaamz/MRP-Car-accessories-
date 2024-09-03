from odoo import models, fields, api
from datetime import date
import logging



from odoo import models, fields, api



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals['order_id']['partner_id']['country_id']['code']== 'US':
                self._apply_conversion(vals)
            else :
                pass
        
        return super(SaleOrderLine, self).create(vals_list)

    def write(self, vals):
        if 'price_unit' in vals or 'order_id' in vals:
            # Appliquer la conversion si le prix unitaire ou l'ordre est mis à jour
            for line in self:
                if vals['order_id']['partner_id']['country_id']['code']== 'US':
                    line_vals = {
                        'price_unit': vals.get('price_unit', line.price_unit),
                        'order_id': vals.get('order_id', line.order_id.id),
                    }
                    
                    self._apply_conversion(line_vals)
                    vals.update(line_vals)
                else:
                    pass
                
        return super(SaleOrderLine, self).write(vals)

    def _apply_conversion(self, vals):
        order = self.env['sale.order'].browse(vals['order_id'])

        # Vérifier si le partenaire est basé aux États-Unis
        if order.partner_id.country_id.code == 'US':
            usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)

            if usd_currency :
                today = date.today()
                # Chercher le taux du jour ou le plus récent
                rate_record = usd_currency.rate_ids.filtered(lambda r: r.name == today)
                if not rate_record:
                    rate_record = usd_currency.rate_ids.sorted(key=lambda r: r.name, reverse=True)[:1]

                if rate_record:
                    usd_to_cad_rate = rate_record.inverse_company_rate

                    # Conversion du price_unit en CAD
                    vals['price_unit'] = vals['price_unit'] * usd_to_cad_rate
        else:
            pass



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create(self, vals):
        order = super(SaleOrder, self).create(vals)
        if self.partner_id.country_id.code == 'US':
            order._add_global_discount_line()
        return order

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        for order in self:
            if order.partner_id.country_id.code == 'US':
                order._add_global_discount_line()
        return res

    def _add_global_discount_line(self):
        # Rechercher le produit de remise globale
        discount_product = self.env['product.product'].search([('name', '=', 'Remise')], limit=1)
        discount_amount = 0.0
        
        total_amount = sum(line.price_subtotal for line in self.order_line)
        
        discount_amount = - (total_amount * 0.75)  # Appliquer la remise de 75%
        
       
        discount_line = self.order_line.filtered(lambda line: line.product_id == discount_product)
        
        if discount_line:
            discount_line.write({
                'price_unit': discount_amount,
                'name':'Remise: 75%',
                    
                })
        else:
            self.order_line.create({
                    'order_id': self.id,
                    'name':'Remise: 75%',
                    'product_id': discount_product.id,
                    'price_unit': discount_amount,
                    'product_uom_qty': 1,
                })
        
