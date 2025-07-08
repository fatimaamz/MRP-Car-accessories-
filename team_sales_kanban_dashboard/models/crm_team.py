from odoo import models, fields, api
from datetime import timedelta

class CrmTeam(models.Model):
    _inherit = "crm.team"

    quote_count = fields.Integer(compute="_compute_sales_stats")
    order_to_invoice_count = fields.Integer(compute="_compute_sales_stats")
    total_sales = fields.Float(compute="_compute_sales_stats")
    sales_by_day = fields.Char(compute="_compute_sales_stats")

    @api.depends("sale_order_ids")
    def _compute_sales_stats(self):
        for team in self:
            today = fields.Date.today()
            past_7 = today - timedelta(days=6)
            sales = self.env['sale.order'].search([
                ('team_id', '=', team.id),
                ('date_order', '>=', past_7)
            ])
            team.quote_count = len(sales.filtered(lambda s: s.state in ['draft', 'sent']))
            team.order_to_invoice_count = len(sales.filtered(lambda s: s.invoice_status == 'to invoice'))
            team.total_sales = sum(sales.filtered(lambda s: s.state in ['sale', 'done']).mapped('amount_total'))

            bars = []
            for i in range(7):
                date = today - timedelta(days=i)
                daily_total = sum(sales.filtered(lambda s: s.date_order.date() == date).mapped('amount_total'))
                bars.append(str(int(daily_total)))
            team.sales_by_day = ','.join(reversed(bars))
