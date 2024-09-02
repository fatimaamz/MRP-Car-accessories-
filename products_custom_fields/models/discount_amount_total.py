from odoo import models, fields, api
from datetime import date
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    amount_total = fields.Monetary(string="Total", store=True, compute='_compute_amounts', tracking=4)

    
    @api.depends('order_line.price_subtotal', 'order_line.price_tax', 'order_line.price_total')
    def _compute_amounts(self):
        """Compute the total amounts of the SO."""
        for order in self:
            order = order.with_company(order.company_id)
            order_lines = order.order_line.filtered(lambda x: not x.display_type)

            if order.company_id.tax_calculation_rounding_method == 'round_globally':
                tax_results = order.env['account.tax']._compute_taxes([
                    line._convert_to_tax_base_line_dict()
                    for line in order_lines
                ])
                totals = tax_results['totals']
                amount_untaxed = totals.get(order.currency_id, {}).get('amount_untaxed', 0.0)
                amount_tax = totals.get(order.currency_id, {}).get('amount_tax', 0.0)
            else:
                amount_untaxed = sum(order_lines.mapped('price_subtotal'))
                amount_tax = sum(order_lines.mapped('price_tax'))

            order.amount_untaxed = amount_untaxed
            order.amount_tax = amount_tax
            order.amount_total = order.amount_untaxed + 1000

    

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
                        conversion = 0.75 * rate_record.rate 
                        
                       
                        order.amount_total = (order.amount_untaxed * conversion) + order.amount_tax
                        _logger.warning("USD conversion done. New Total: %s", order.amount_total)
       """

   
     
