# -*- coding: utf-8 -*-

from odoo import models,fields,api


class CustomProductProduct(models.Model):
    _inherit = 'product.product'

    @api.depends('name', 'default_code', 'product_tmpl_id', 'product_template_attribute_value_ids')
    @api.depends_context('display_default_code', 'seller_id', 'company_id', 'partner_id')
    def _compute_display_name(self):
        def get_display_name(name, code):
            if self._context.get('display_default_code', True) and code:
                return f'[{code}] {name}'
            return name

        for product in self:
            # Dictionaries to hold attributes with single and multiple values
            attribute_values = {}
            single_value_attributes = []
            multiple_value_attributes = []

            # Group attribute values by their attribute
            for variant_value in product.product_template_attribute_value_ids:
                attribute = variant_value.attribute_id
                if attribute not in attribute_values:
                    attribute_values[attribute] = []
                attribute_values[attribute].append(variant_value)

            # Separate single and multiple value attributes
            for attribute, values in attribute_values.items():
                if len(values) == 1:
                    single_value_attributes.append(f"{attribute.name}: {values[0].name}")
                else:
                    values_str = ", ".join(v.name for v in values)
                    multiple_value_attributes.append(f"{attribute.name}: {values_str}")

            # Combine the names of single and multiple value attributes
            name = product.name
            if single_value_attributes:
                name += " [" + ", ".join(single_value_attributes) + "]"
            if multiple_value_attributes:
                name += " (" + ", ".join(multiple_value_attributes) + ")"

            partner_id = self._context.get('partner_id')
            partner_ids = [partner_id, self.env['res.partner'].browse(partner_id).commercial_partner_id.id] if partner_id else []

            # Retrieve supplier information based on context and partner IDs
            sellers = self.env['product.supplierinfo'].sudo().browse(self.env.context.get('seller_id')) or []
            if not sellers and partner_ids:
                product_supplier_info = self.env['product.supplierinfo'].sudo().search([
                    ('product_tmpl_id', '=', product.product_tmpl_id.id),
                    ('partner_id', 'in', partner_ids)
                ])
                sellers = product_supplier_info.filtered(lambda s: not s.product_id or s.product_id == product)

            # Construct display name using supplier info if available
            if sellers:
                temp = []
                for s in sellers:
                    seller_variant = s.product_name and f"{s.product_name} ({name})" or False
                    temp.append(get_display_name(seller_variant or name, s.product_code or product.default_code))
                product.display_name = ", ".join(set(temp))  # Ensure uniqueness in the list
            else:
                product.display_name = get_display_name(name, product.default_code)

class YearModel(models.Model):
    _name = 'year.model'
    _description = 'Year Model'

    name = fields.Integer(string='Année', required=True, unique=True)


class ProductMark(models.Model):
    _name = 'product.modele'
    _description = 'Product model'

    name = fields.Char(string='model', required=True)
class ProductSousModele(models.Model):
    _name = 'product.sousmodele'
    _description = 'Product Sous modele'

    name = fields.Char(string='Sous modèle', required=True)

class ProductStyle(models.Model):
    _name = 'product.style'
    _description = 'Product Style'

    name = fields.Char(string='Name', required=True)
class ProductMarque(models.Model):
    _name = 'product.marque'
    _description = 'Product Brand'

    name = fields.Char(string='Name', required=True)
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    year_ids = fields.Many2many('year.model', string='Année')
    product_type = fields.Selection([
        ('Exterior', 'Exterior'),
        ('Moulding', 'Moulding'),
        ('Interior', 'Interior'),
        ('Grill', 'Grill')
    ], string='Type')

    priceA = fields.Float(string='Prix A')
    priceB = fields.Float(string='Prix B')
    priceC = fields.Float(string='Prix C')
    priceD = fields.Float(string='Prix D')

    modele_id = fields.Many2one('product.modele', string='Modèle')
    sous_model_id = fields.Many2one('product.sousmodele', string='Sous modèle')
    style_id = fields.Many2one('product.style', string='Style')
    marque_id = fields.Many2one('product.marque', string='Marque')
