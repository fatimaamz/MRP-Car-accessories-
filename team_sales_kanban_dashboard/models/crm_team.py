from odoo import models, fields, api
from datetime import datetime, timedelta

class CrmTeam(models.Model):
    _inherit = "crm.team"

    quote_count = fields.Integer(string="Nombre de devis (7j)", compute="_compute_sales_stats", store=False)
    order_count = fields.Integer(string="Commandes confirmées (7j)", compute="_compute_sales_stats", store=False)
    total_sales = fields.Float(string="Total ventes (7j)", compute="_compute_sales_stats", store=False)
    sales_by_day = fields.Char(string="Ventes quotidiennes", compute="_compute_sales_stats", store=False)

    @api.depends()
    def _compute_sales_stats(self):
        today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = today - timedelta(days=6)  # 7 jours en arrière
        end_date = today + timedelta(days=1)

        for team in self:
            SaleOrder = self.env['sale.order']

            # 1. Devis (état = draft ou sent)
            quotes = SaleOrder.search([
                ('team_id', '=', team.id),
                ('date_order', '>=', start_date),
                ('date_order', '<', end_date),
                ('state', 'in', ['draft', 'sent'])
            ])

            # 2. Commandes confirmées (sale)
            orders = SaleOrder.search([
                ('team_id', '=', team.id),
                ('date_order', '>=', start_date),
                ('date_order', '<', end_date),
                ('state', '=', 'sale')
            ])

            team.quote_count = len(quotes)
            team.order_count = len(orders)
            team.total_sales = sum(orders.mapped('amount_total'))

            # 3. Barres par jour : ventes des commandes confirmées uniquement
            bars = []
            for i in range(7):
                day_start = today - timedelta(days=i)
                day_end = day_start + timedelta(days=1)

                day_orders = SaleOrder.search([
                    ('team_id', '=', team.id),
                    ('date_order', '>=', day_start),
                    ('date_order', '<', day_end),
                    ('state', '=', 'sale')
                ])
                daily_total = sum(day_orders.mapped('amount_total'))
                bars.append(str(int(daily_total)))

            team.sales_by_day = ','.join(reversed(bars))
