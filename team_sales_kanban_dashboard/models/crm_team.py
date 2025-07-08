from odoo import models, fields, api
from datetime import timedelta

class CrmTeam(models.Model):
    _inherit = "crm.team"

    order_count = fields.Integer(string="Commandes confirmées", compute="_compute_sales_stats", store=False)
    total_sales = fields.Float(string="Total ventes", compute="_compute_sales_stats", store=False)
    sales_by_day = fields.Char(string="Ventes quotidiennes", compute="_compute_sales_stats", store=False)

    @api.depends()
    def _compute_sales_stats(self):
        today = fields.Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start = today - timedelta(days=6)
        end = today + timedelta(days=1)
    
        for team in self:
            orders = self.env['sale.order'].search([
                ('team_id', '=', team.id),
                ('date_order', '>=', start),
                ('date_order', '<', end),
                ('state', 'in', ['sale', 'done']),
            ])
            team.order_count = len(orders)
            team.total_sales = sum(orders.mapped('amount_total'))
    
            # Ventes par jour (7 derniers jours)
            daily = []
            for i in range(7):
                day_start = today - timedelta(days=i)
                day_end = day_start + timedelta(days=1)
                daily_total = sum(
                    orders.filtered(lambda o: day_start <= o.date_order < day_end).mapped('amount_total')
                )
                daily.append(str(int(daily_total)))
            team.sales_by_day = ','.join(reversed(daily))
