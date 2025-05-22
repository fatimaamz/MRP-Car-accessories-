from odoo import http
from odoo.http import request

class PublicPickingReportController(http.Controller):

    @http.route('/report/pdf/lux_contacts_custom_fields.report_deliveryslip_new_template/<int:picking_id>', type='http', auth='public', website=True)
    def picking_pdf(self, picking_id, **kwargs):
        # Vérifier access token pour autoriser l'accès
        access_token = request.params.get('access_token') or request.httprequest.args.get('access_token')
        picking = request.env['stock.picking'].sudo().search([('id', '=', picking_id), ('access_token', '=', access_token)])

        if not picking:
            return request.not_found()

        pdf_content, _ = request.env.ref('lux_contacts_custom_fields.action_report_deliveryslip_new_template').sudo()._render_qweb_pdf([picking_id])
        headers = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf_content))]
        return request.make_response(pdf_content, headers=headers)
