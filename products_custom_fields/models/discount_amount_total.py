from odoo import models, fields, api,_
from datetime import date
import logging

_logger = logging.getLogger(__name__)

"""
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

"""
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

    def _update_total_amount_based_on_shipping_country(self):
        for order in self:
            if order.partner_shipping_id:
                country_code = order.partner_shipping_id.country_id.code

                # Get the USD currency
                usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)

                if usd_currency:
                    today = date.today()
                    rate_record = usd_currency.rate_ids.filtered(lambda r: r.name == today)
                    if not rate_record:
                        rate_record = usd_currency.rate_ids.sorted(key=lambda r: r.name, reverse=True)[:1]

                    if rate_record:
                        usd_to_cad_rate = float(rate_record.inverse_company_rate)

                        # Calculate the new total based on country
                        if country_code == 'US':
                            new_total = sum(line.price_subtotal * usd_to_cad_rate * 0.75 for line in order.order_line)
                        else:
                            new_total = sum(line.price_subtotal * 0.75 for line in order.order_line)

                        if order.amount_total != new_total:
                            _logger.info(f"Updating total amount from {order.amount_total} to {new_total} for order {order.id}")
                            order.amount_total = new_total

    @api.model
    def create(self, vals):
        order = super(SaleOrder, self).create(vals)
        order._update_total_amount_based_on_shipping_country()
        return order

    def write(self, vals):
        result = super(SaleOrder, self).write(vals)
        # Avoid recursive call if amount_total is already being updated
        if 'amount_total' not in vals:
            self._update_total_amount_based_on_shipping_country()
        return result
   
    """


    @api.depends('order_line.price_subtotal', 'order_line.price_tax', 'order_line.price_total', 'partner_shipping_id.country_id')
    def _compute_amounts(self):
        """Compute the total amounts of the SO and apply discounts and conversions based on shipping country."""
        for order in self:
            order = order.with_company(order.company_id)
            order_lines = order.order_line.filtered(lambda x: not x.display_type)

            # Calculate untaxed and tax amounts
            if order.company_id.tax_calculation_rounding_method == 'round_globally':
                tax_results = order.env['account.tax']._compute_taxes([line._convert_to_tax_base_line_dict() for line in order_lines])
                totals = tax_results['totals']
                amount_untaxed = totals.get(order.currency_id, {}).get('amount_untaxed', 0.0)
                amount_tax = totals.get(order.currency_id, {}).get('amount_tax', 0.0)
            else:
                amount_untaxed = sum(order_lines.mapped('price_subtotal'))
                amount_tax = sum(order_lines.mapped('price_tax'))

            order.amount_untaxed = amount_untaxed
            order.amount_tax = amount_tax

            # Currency conversion and discount logic
            if order.partner_shipping_id:
                country_code = order.partner_shipping_id.country_id.code

                # Get the USD currency
                usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)

                if usd_currency:
                    today = date.today()
                    rate_record = usd_currency.rate_ids.filtered(lambda r: r.name == today)
                    if not rate_record:
                        rate_record = usd_currency.rate_ids.sorted(key=lambda r: r.name, reverse=True)[:1]

                    if rate_record:
                        usd_to_cad_rate = float(rate_record.inverse_company_rate)

                        # Apply discount based on country
                        if country_code == 'US':
                            discount_multiplier = 0.75  # Example discount for US customers
                        else:
                            discount_multiplier = 0.75  # Default discount for other countries

                        # Calculate new total after applying discount and conversion
                        new_total = (amount_untaxed * discount_multiplier) + amount_tax
                        new_total = round(new_total, 2)  # Ensure rounding

                        # Log and update the total if necessary
                        if order.amount_total != new_total:
                            _logger.info(f"Updating total amount from {order.amount_total} to {new_total} for order {order.id}")
                            order.amount_total = new_total
                        else:
                            order.amount_total = amount_untaxed + amount_tax  # Fallback to the original total if no change
            else:
                # If no shipping address, keep the original total
                order.amount_total = amount_untaxed + amount_tax
                
                            
    @api.model
    def create(self, vals):
        order = super(SaleOrder, self).create(vals)
        order._compute_amounts()  # Recompute the amount after creation
        return order

    def write(self, vals):
        result = super(SaleOrder, self).write(vals)
        if 'order_line' in vals or 'partner_shipping_id' in vals:
            self._compute_amounts()  # Recompute the amount on write if relevant fields are updated
        return result

    
    
   
  
   
 
    

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

  
