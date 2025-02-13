from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountInvoiceReportWizard(models.TransientModel):
    _name = 'account.invoice.report.wizard'
    _description = "Wizard to generate customer invoice reports"

    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner', string="Customer", domain=[('customer_rank', '>', 0)], required=True)
    date_start = fields.Date(string="Start Date", required=True)
    date_end = fields.Date(string="End Date", required=True)

    def action_print_report(self):
        if self.date_start > self.date_end:
            raise UserError("The start date must be before the end date.")

        return self.env.ref('lux_contacts_custom_fields.action_invoice_report').report_action(self)


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
            'data': data,
            'docs': invoices,
        }
