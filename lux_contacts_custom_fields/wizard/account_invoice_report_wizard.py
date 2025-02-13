from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime

class AccountInvoiceReportWizard(models.TransientModel):
    _name = 'account.invoice.report.wizard'
    _description = "Wizard to generate customer invoice reports"

    company_id = fields.Many2one('res.company', string="Société", required=True, default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner', string="Client", domain=[('customer_rank', '>', 0)], required=True)
    date_start = fields.Date(string="Date De Début", required=True)
    date_end = fields.Date(string="Date De Fin", required=True)
    
   

    def action_print_report(self):
        if self.date_start > self.date_end:
            raise UserError("The start date must be before the end date.")
        #data = self.get_invoice_report_data()
        return self.env.ref('lux_contacts_custom_fields.action_invoice_report').report_action(self)
    """
    def get_invoice_report_data(self):
       
        invoices = self.env['account.move'].search([
            ('partner_id', '=', self.partner_id.id),
            ('move_type', '=', 'out_invoice'),
            ('invoice_date', '>=', self.date_start),
            ('invoice_date', '<=', self.date_end),
            ('company_id', '=', self.company_id.id),
            ('state', '=', 'posted')
        ])
        return {
            'partner_id': self.partner_id.name,
            'company_id': self.company_id.name,
            'date_start': self.date_start,
            'date_end': self.date_end,
            'invoices': invoices,
            'date_today': datetime.today().strftime('%d/%m/%Y'),
        }
        
   """


class AccountInvoiceReport(models.AbstractModel):
    _name = 'report.lux_contacts_custom_fields.invoice_report_template'
    _description = "Customer Invoice Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        wizard = self.env['account.invoice.report.wizard'].browse(docids)
        invoices = self.env['account.move'].search([
            ('partner_id', '=', wizard.partner_id.id),
            ('move_type', '=', 'out_invoice'),
            ('invoice_date', '>=', wizard.date_start),
            ('invoice_date', '<=', wizard.date_end),
            ('company_id', '=', wizard.company_id.id),
            ('state', '=', 'posted')
        ])
        return {
            'doc_ids': docids,
            'doc_model': 'account.invoice.report.wizard',
            'data': {  # Add the wizard dates to data
                    'date_start': wizard.date_start,
                    'date_end': wizard.date_end,
                    'partner_id':wizard.partner_id.name,
                    'company_id':wizard.company_id.name,
                },
            'docs': invoices,
        }

