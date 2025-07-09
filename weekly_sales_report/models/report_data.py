from odoo import models, fields, api
from datetime import timedelta

class ReportSalesTeamWeekly(models.AbstractModel):
    _name = 'report.weekly_sales_report.report_sales_team_weekly'
    _description = 'Weekly Sales Team Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        today = fields.Date.today()
        start_date = today - timedelta(days=7)
        teams = self.env['crm.team'].browse(docids)
        results = []

        for team in teams:
            orders = self.env['sale.order'].search([
                ('team_id', '=', team.id),
                ('date_order', '>=', start_date),
                ('date_order', '<=', today),
                ('state', 'in', ['sale', 'done'])
            ])
            total = sum(orders.mapped('amount_total'))
            count = len(orders)
            dropship_total = sum(orders.filtered(lambda o: 'drop' in o.name.lower()).mapped('amount_total'))
            bonus = total * 0.02
            last_year = today.replace(year=today.year - 1)
            last_year_orders = self.env['sale.order'].search([
                ('team_id', '=', team.id),
                ('date_order', '>=', last_year - timedelta(days=7)),
                ('date_order', '<=', last_year),
                ('state', 'in', ['sale', 'done'])
            ])
            last_year_total = sum(last_year_orders.mapped('amount_total'))
            results.append({
                'team_name': team.name,
                'target': 10000,
                'total': total,
                'percent': round((total / 10000) * 100) if total else 0,
                'bonus': round(bonus, 2),
                'dropship': dropship_total,
                'count': count,
                'lux_clients': 13,
                'oem_clients': 4,
                'last_year_total': last_year_total,
                'this_year_total': total,
                'start_date': start_date,
                'end_date': today
            })

        return {
            'doc_ids': docids,
            'doc_model': 'crm.team',
            'docs': teams,
            'data': results
        }
