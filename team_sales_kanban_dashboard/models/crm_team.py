from odoo import models, fields, api
from datetime import datetime, timedelta

from odoo import models, fields, api
from datetime import datetime, timedelta

from odoo import models, fields, api
from datetime import datetime, timedelta

class CrmTeam(models.Model):
    _inherit = "crm.team"

    dashboard_graph_data_7d = fields.Binary(
        string="Dashboard Graph (7d)",
        compute="_compute_dashboard_graph_data_7d"
    )

    @api.depends()
    def _compute_dashboard_graph_data_7d(self):
        for team in self:
            now = fields.Datetime.now()
            date_7_days_ago = now - timedelta(days=7)

            # Lecture des commandes sur les 7 derniers jours
            orders = self.env['sale.order'].search([
                ('team_id', '=', team.id),
                ('date_order', '>=', date_7_days_ago),
                ('state', 'in', ['sale', 'done']),
            ])

            # Groupement manuel par jour
            data_per_day = {}
            for order in orders:
                day = order.date_order.date().strftime('%Y-%m-%d')
                data_per_day.setdefault(day, 0)
                data_per_day[day] += order.amount_total

            # Convertir les données pour le widget graphique
            graph_data = {
                'title': 'Commandes - 7 derniers jours',
                'x_axis': 'Jour',
                'y_axis': 'Montant',
                'groups': [{'date_order': day, 'amount_total': total} for day, total in sorted(data_per_day.items())],
                'graph_type': 'bar'
            }

            team.dashboard_graph_data_7d = graph_data
