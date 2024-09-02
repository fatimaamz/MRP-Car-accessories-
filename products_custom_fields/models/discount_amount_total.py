from odoo import models, fields, api
from datetime import date
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    amount_total = fields.Monetary(
        string='Total',
        store=True, 
        readonly=True, 
        compute='_compute_amount_total'
    )

    

    @api.depends('order_line.price_total', 'additional_amount')
    def _compute_amount_total(self):
        for order in self:
            total = sum(order.order_line.mapped('price_total'))
            # Add custom additional amount to the total
            order.amount_total = total + 200


    """
    @api.depends('order_line.price_total')
    def _compute_amount(self):
        super(SaleOrder, self)._compute_amount()
        
        for order in self:
            if order.partner_id.country_id.code == 'US':
                usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
                
                if usd_currency:
                    today = date.today()
                    
                    rate_record = usd_currency.rate_ids.filtered(lambda r: r.name == today)

                    if not rate_record:
                        rate_record = usd_currency.rate_ids.sorted(key=lambda r: r.name, reverse=True)[:1]

                    if rate_record:
                        conversion = 0.75 * rate_record.rate  # Apply 75% discount
                        
                       
                        order.amount_total = (order.amount_untaxed * conversion) + order.amount_tax
                        _logger.warning("USD conversion done. New Total: %s", order.amount_total)
            return res 
"""
   
     
