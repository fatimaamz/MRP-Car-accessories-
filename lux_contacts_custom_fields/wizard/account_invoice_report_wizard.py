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

        return self.env.ref('your_module_name.action_invoice_report').report_action(self)
