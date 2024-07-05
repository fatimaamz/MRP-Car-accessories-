# -*- coding: utf-8 -*-

from odoo import models,fields,api
class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    def _compute_has_configurable_attributes(self):
        """A product is considered configurable if:
        - It has dynamic attributes
        - It has any attribute line with at least 2 attribute values configured
        - It has multi-checkbox display type
        - It has at least one custom attribute value
        """
        for product in self:
            product.has_configurable_attributes = (
                product.has_dynamic_attributes() or any(
                    ptal.attribute_id.display_type == 'multi'
                    or len(ptal.value_ids) >= 1
                    or ptal.value_ids.is_custom
                    for ptal in product.attribute_line_ids
                )
            )
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
