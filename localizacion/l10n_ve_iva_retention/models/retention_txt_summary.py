from odoo import fields, models
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)


class RetentionTxtSummary(models.Model):
    _name = 'retention.txt.summary'
    _description = 'Resume txt retencion'
    _rec_name = 'id'

    from_date = fields.Date(string='Desde', default=lambda *a: datetime.now().strftime('%Y-%m-%d'), copy=False)
    to_date = fields.Date('Hasta', default=lambda *a: (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                          copy=False)
    state = fields.Selection([('draft', 'Borrador'), ('pre_post', 'TXT en Proceso'), ('generada', 'TXT Generado')],
                             copy=False)
    attachment_ids = fields.Many2many(string='Attachments', comodel_name='ir.attachment',
                                      relation='sumary_retention_txt_rel', column1='sumary_retention_txt_id',
                                      column2='attachment_id', copy=False)
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.user.company_id.id, readonly=True, copy=False)
    line_ids = fields.One2many('retention.txt.summary.line', 'sumary_retention_txt_id', string='Retention Lines',
                               copy=False, readonly=True)


class RetentionTxtSummaryLine(models.Model):
    _name = "retention.txt.summary.line"
    _description = 'lineas de Resume txt retencion'
    _rec_name = 'id'

    sumary_retention_txt_id = fields.Many2one('retention.txt.summary', string='Declaracion', copy=False)
    rif_retenido = fields.Char(string='RIF Retenido', copy=False)
    numero_factura = fields.Char(string='Número de Factura', copy=False)
    numero_control = fields.Char(string='Número de Control', copy=False)
    codigo_concepto = fields.Char(string='Codigo concepto', copy=False)
    fecha_operacion = fields.Date(string='Fecha de Operación', copy=False)
    amount_retention = fields.Char(string='Porcentaje de Retención', copy=False)
    amount_untaxed = fields.Char(string='Monto retencion', copy=False)
    amount_tax = fields.Char(string='Impuesto de Retención', copy=False)
