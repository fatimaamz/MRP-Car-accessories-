from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime

class AccountInvoiceReportWizard(models.TransientModel):
    _name = 'account.invoice.report.wizard'
    _description = "Wizard to generate customer invoice reports"

    company_id = fields.Many2one('res.company', string="Société", required=True, default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner', string="Client")
    date_start = fields.Date(string="Date De Début", required=True)
    date_end = fields.Date(string="Date De Fin", required=True)
    all_partners = fields.Boolean(string="Toutes", help="Sélectionner pour inclure tous les clients")
    paid_only = fields.Boolean(string="Factures Payées Seulement", help="Inclure uniquement les factures entièrement payées")

    
   

    def action_print_report(self):
        if self.date_start > self.date_end:
            raise UserError("The start date must be before the end date.")
        #data = self.get_invoice_report_data()
        return self.env.ref('lux_contacts_custom_fields.action_invoice_report').report_action(self)



class AccountInvoiceReport(models.AbstractModel):
    _name = 'report.lux_contacts_custom_fields.invoice_report_template'
    _description = "Customer Invoice Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        if not docids:
            return {}

        wizard = self.env['account.invoice.report.wizard'].browse(docids[0])  # Use the first wizard record
        domain = [
            ('move_type', '=', 'out_invoice'),
            ('invoice_date', '>=', wizard.date_start),
            ('invoice_date', '<=', wizard.date_end),
            ('company_id', '=', wizard.company_id.id),
            ('state', '=', 'posted')
        ]

        if wizard.paid_only:
            domain.append(('payment_state', 'in', ['paid', 'in_payment']))  # Factures payées ou en paiement

        if not wizard.all_partners and wizard.partner_id:
            domain.append(('partner_id', '=', wizard.partner_id.id))

        invoices = self.env['account.move'].search(domain)

        # Group invoices by partner (client)
        grouped_invoices = {}
        for invoice in invoices:
            grouped_invoices.setdefault(invoice.partner_id, []).append(invoice)

        return {
            'doc_ids': docids,
            'doc_model': 'account.invoice.report.wizard',
            'data': {
                'date_start': wizard.date_start,
                'date_end': wizard.date_end,
                'partner_id': wizard.partner_id.name if not wizard.all_partners else 'All Customers',
                'company_id': wizard.company_id.name,
                'grouped_invoices': grouped_invoices,
                'date_today': datetime.today().strftime('%d/%m/%Y'),
            },
        }
    
    """
    @api.model
    def _get_report_values(self, docids, data=None):
        wizard = self.env['account.invoice.report.wizard'].browse(docids)
        domain = [
            ('move_type', '=', 'out_invoice'),
            ('invoice_date', '>=', wizard.date_start),
            ('invoice_date', '<=', wizard.date_end),
            ('company_id', '=', wizard.company_id.id),
            ('state', '=', 'posted')
        ]

        if wizard.all_partners:
            # Include all partners when "Toutes" is selected
            invoices = self.env['account.move'].search(domain)
        else:
            # Filter by the selected partner
            invoices = self.env['account.move'].search(domain + [('partner_id', '=', wizard.partner_id.id)])

        # Group invoices by partner (client)
        grouped_invoices = {}
        for invoice in invoices:
            if invoice.partner_id not in grouped_invoices:
                grouped_invoices[invoice.partner_id] = []
            grouped_invoices[invoice.partner_id].append(invoice)

        return {
            'doc_ids': docids,
            'doc_model': 'account.invoice.report.wizard',
            'data': {
                'date_start': wizard.date_start,
                'date_end': wizard.date_end,
                'partner_id': wizard.partner_id.name if not wizard.all_partners else 'All Customers',
                'company_id': wizard.company_id.name,
                'grouped_invoices': grouped_invoices,
                'date_today': datetime.today().strftime('%d/%m/%Y'),
            },
        }
"""
