from odoo import models, fields, api
from datetime import datetime, timedelta



class CrmTeam(models.Model):
    _inherit = "crm.team"
    
    test_dashboard_data = fields.Binary(
    compute="_compute_test_dashboard_data",
    store=False
    )

    @api.depends()
    def _compute_test_dashboard_data(self):
        for team in self:
            team.test_dashboard_data = {
                'title': 'Test',
                'x_axis': 'X',
                'y_axis': 'Y',
                'graph_type': 'bar',
                'groups': [{'x': '1', 'y': 100}, {'x': '2', 'y': 200}],
            }


    dashboard_graph_data_7d = fields.Binary(
        string="Dashboard Graph (7 Days)",
        compute="_compute_dashboard_graph_data_7d",
        store=False
    )

    @api.depends()
    def _compute_dashboard_graph_data_7d(self):
        for team in self:
            now = fields.Datetime.now()
            last_7_days = now - timedelta(days=7)
            orders = self.env['sale.order'].search([
                ('team_id', '=', team.id),
                ('date_order', '>=', last_7_days),
                ('state', 'in', ['sale', 'done'])
            ])
            grouped_data = {}
            for order in orders:
                key = order.date_order.date().strftime('%Y-%m-%d')
                grouped_data.setdefault(key, 0)
                grouped_data[key] += order.amount_total
            graph_data = {
                'title': 'Commandes (7 derniers jours)',
                'x_axis': 'Jour',
                'y_axis': 'Montant total',
                'groups': [{'date_order': day, 'amount_total': total} for day, total in sorted(grouped_data.items())],
                'graph_type': 'bar'
            }
            team.dashboard_graph_data_7d = graph_data or {}
