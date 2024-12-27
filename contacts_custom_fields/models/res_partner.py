from odoo import models, fields

class ResPartner(models.Model):
    _inherit = "res.partner"

    rc = fields.Char(
        string="N° RC",
        help="Numéro du Registre de Commerce"
    )

    nis = fields.Char(
        string="N.I.S",
        help="Numéro d'Identification Statistique"
    )

    ai = fields.Char(
        string="A.I",
        help="Article d’Imposition"
    )

    nif = fields.Char(
        string="N.I.F",
        help="Numéro d'Identification Fiscale"
    )
