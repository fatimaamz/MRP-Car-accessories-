from odoo import http
from odoo.http import request

class PublicReportController(http.Controller):

    @http.route('/public/report/deliveryslip/<int:picking_id>', type='http', auth='public', website=True)
    def public_deliveryslip(self, picking_id, **kwargs):
        picking = request.env['stock.picking'].sudo().browse(picking_id)
        if not picking.exists():
            return request.not_found()

        pdf_content, _ = request.env.ref(
            'lux_contacts_custom_fields.action_report_deliveryslip_new_template'
        ).sudo()._render_qweb_pdf([picking_id])

        pdf_http_headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf_content)),
        ]
        return request.make_response(pdf_content, headers=pdf_http_headers)
