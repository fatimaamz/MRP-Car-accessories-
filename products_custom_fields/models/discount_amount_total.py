from odoo import models, fields, api,_
from datetime import date
import logging


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model_create_multi
    def create(self, vals_list):
        orders = self.env['sale.order'].browse([vals['order_id'] for vals in vals_list])
        for vals, order in zip(vals_list, orders):
            self._apply_conversion(vals)
        
        return super(SaleOrderLine, self).create(vals_list)

    def write(self, vals):
        if 'price_unit' in vals or 'order_id' in vals:
            for line in self:
                line_vals = {
                        'price_unit': vals.get('price_unit', line.price_unit),
                        'order_id': vals.get('order_id', line.order_id.id),
                    }
                self._apply_conversion(line_vals)
                vals.update(line_vals)
                
        return super(SaleOrderLine, self).write(vals)
        
   
    def _apply_conversion(self, vals):
        order = self.env['sale.order'].browse(vals.get('order_id'))
    
        # Check if the partner is based in the US
        if order.shopify_instance_id.id == 1 and order.partner_id.country_id.code == 'US':
            product_template_id = vals.get('product_template_id', {}).get('name')
            
            if product_template_id != 'discount':
                usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
                
                if usd_currency:
                    today = date.today()
                    rate_record = usd_currency.rate_ids.filtered(lambda r: r.name == today)
                    if not rate_record:
                        rate_record = usd_currency.rate_ids.sorted(key=lambda r: r.name, reverse=True)[:1]
    
                    if rate_record:
                        usd_to_cad_rate = float(rate_record.inverse_company_rate)
                        vals['price_unit'] = float(vals.get('price_unit', 0)) * usd_to_cad_rate * 0.75
                        
        elif order.shopify_instance_id.id == 1 and order.partner_id.country_id.code != 'US':
            product_template_id = vals.get('product_template_id', {}).get('name')
            
            if product_template_id != 'discount':
                vals['price_unit'] = float(vals.get('price_unit', 0)) * 0.75


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
   

    state = fields.Selection(selection_add=[
        ('design',  _('Désign'))
    ])
    order_source = fields.Selection([
        ('shopify', 'Shopify'),
        ('whatsapp', 'WhatsApp'),
        
    ], string='order Source',compute='_compute_order_source')

    from_whatsapp = fields.Boolean(string="Whatsapp", default=False)

    
    
    
   
    """
    @api.depends('order_source', 'shopify_instance_id')
    def _compute_partner_id(self):
        for rec in self:
            current_partner_id = rec.partner_id.id  
            
           
            if rec.order_source == 'shopify':
                if rec.shopify_instance_id == 1:
                    designer_trim_partner = self.env['res.partner'].search([('name', '=', 'DESIGNER TRIM')], limit=1)
                    if designer_trim_partner:
                        rec.partner_id = designer_trim_partner.id
                        
                if rec.shopify_instance_id == 2:
                    luxwood_retailer_partner = self.env['res.partner'].search([('name', '=', 'LUXWOOD RETAILER')], limit=1)
                    if luxwood_retailer_partner:
                        rec.partner_id = luxwood_retailer_partner.id
            elif rec.order_source == 'whatsapp':
                luxwood_rep_partner = self.env['res.partner'].search([('name', '=', 'LUXWOOD REP')], limit=1)
                if luxwood_rep_partner:
                    rec.partner_id = luxwood_rep_partner.id
              
            else:
               rec.partner_id = current_partner_id
                
    def create(self, vals):
        # Call super to create the order first
        order = super(SaleOrder, self).create(vals)

        # Recompute the partner_id after creation
        order._compute_partner_id()
        return order
    

    """
   



   
 
    

    def _can_be_confirmed(self):
        self.ensure_one()
        # Ajout de l'état 'design' comme état pouvant être confirmé
        return self.state in {'draft', 'sent', 'design'}
    

    @api.model
    def _default_state_selection(self):
        return [
            ('draft', _('Devis')),
            ('sent', _('Envoyé')),
            ('design', _('Désign')),  # Ajoutez _() pour la traduction
            ('sale', _('Bon de commande')),
            ('cancel', _('Annulé'))
        ]

    state = fields.Selection(selection=_default_state_selection, string=_("Statut"), readonly=True, copy=False, index=True, tracking=3, default='draft')
    
    def _compute_order_source(self):
        for order in self:
            if order.shopify_instance_id:
                if order.shopify_instance_id.id == 1 or order.shopify_instance_id.id == 2 : 
                    order.order_source = 'shopify'
                
                else:
                    order.order_source = False
            elif order.from_whatsapp == True:
                order.order_source = 'whatsapp'
            else:
                 order.order_source = False
    

    def action_set_design(self):
        self.state = 'design'

  
