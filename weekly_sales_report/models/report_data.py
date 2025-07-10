from odoo import models, fields, api
from datetime import timedelta

class ReportSalesTeamStats(models.AbstractModel):
    _name = 'report.weekly_sales_report.sales_team_report'
    _description = 'Rapport PDF des statistiques par équipe commerciale'


    @api.model
    def _get_report_values(self, docids, data=None):
        today = fields.Date.today()
        last_week = today - timedelta(days=7)

        teams = self.env['crm.team'].browse(docids)
        result = []

        for team in teams:
            orders = self.env['sale.order'].search([
                ('team_id', '=', team.id),
                ('state', 'in', ['sale', 'done']),
                ('date_order', '>=', last_week),
            ])
            sales_total = sum(orders.mapped('amount_total'))
            order_count = len(orders)

            customers = self.env['res.partner'].search_count([
                ('team_id', '=', team.id),
                ('customer_rank', '>', 0)
            ])

            result.append({
                'name': team.name,
                'weekly_sales': sales_total,
                'weekly_target': team.weekly_target,
                'invoicing_target': team.invoiced_target,
                'customer_count': customers,
                'order_count': order_count,
            })

        return {
            'doc_ids': docids,
            'doc_model': 'crm.team',
            'teams': result,
        }


   

        
