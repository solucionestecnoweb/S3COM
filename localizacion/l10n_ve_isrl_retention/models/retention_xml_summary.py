from odoo import fields, models
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import logging
import base64

_logger = logging.getLogger(__name__)


class RetentionXmlSummary(models.Model):
    _name = 'retention.xml.summary'
    _description = 'Resume xml retencion'
    _rec_name = 'id'

    from_date = fields.Date(string='Desde', default=lambda *a: datetime.now().strftime('%Y-%m-%d'), copy=False)
    to_date = fields.Date('Hasta', default=lambda *a: (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                          copy=False)
    state = fields.Selection([('xml_draft', 'XML Borrador'), ('xml_generado', 'XML Generado')], copy=False,
                             default='xml_draft')
    attachment_ids = fields.Many2many(string='Attachments', comodel_name='ir.attachment',
                                      relation='sumary_retention_rel', column1='sumary_retention_id',
                                      column2='attachment_id', copy=False)
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.user.company_id.id, readonly=True, copy=False)
    line_ids = fields.One2many('retention.xml.summary.line', 'sumary_retention_id', string='Retention Lines',
                               copy=False)

    def action_post_xml(self):
        element = ET.Element('RelacionRetencionesISLR', RifAgente=self.env.company.doc_type + '' + self.env.company.vat,
                             Periodo=str(self.from_date.year))
        for ret_line in self.line_ids:
            element_child_1 = ET.SubElement(element, 'DetalleRetencion')

            ET.SubElement(element_child_1, 'RifRetenido').text = ret_line.rif_retenido

            ET.SubElement(element_child_1, 'NumeroFactura').text = ret_line.numero_factura if ret_line.numero_factura \
            else '0'

            ET.SubElement(element_child_1, 'NumeroControl').text = ret_line.numero_control if ret_line.numero_control \
                else ret_line.numero_control_unico

            ET.SubElement(element_child_1, 'FechaOperacion').text = str(ret_line.fecha_operacion)
            ET.SubElement(element_child_1, 'CodigoConcepto').text = ret_line.codigo_concepto

            ET.SubElement(element_child_1, 'MontoOperacion').text = ret_line.monto_operacion

            ET.SubElement(element_child_1, 'PorcentajeRetencion').text = ret_line.porcentaje_retencion
        tree = ET.ElementTree(element)
        tree.write('islr.xml', encoding='utf-8', xml_declaration=True)

        xml = open('islr.xml')
        out = xml.read()
        base64.b64encode(bytes(out, 'utf-8'))
        action = self.env.ref('l10n_ve_isrl_retention.action_account_xml_download_wizard').read()[0]
        ids = self.env['islr.xml.download.wizard'].create({
           'report': base64.b64encode(bytes(out, 'utf-8')),
           'name': 'islr.xml'
        })

        attachment = self.env['ir.attachment'].create({
           'name': 'Resumen {0}-{1}.xml'.format(str(self.from_date), str(self.to_date)),
           'res_id': self.id,
           'res_model': 'retention.xml.summary',
           'datas': base64.b64encode(bytes(out, 'utf-8')),
           'type': 'binary',
        })
        self.write({'attachment_ids': attachment.ids, 'state': 'xml_generado'})
        action['res_id'] = ids.id
        return action


class RetentionXmlSummaryLine(models.Model):
    _name = "retention.xml.summary.line"
    _description = 'lineas de Resume xml retencion'
    _rec_name = 'id'

    sumary_retention_id = fields.Many2one('retention.xml.summary', string='Declaracion', copy=False)
    rif_retenido = fields.Char(string='RIF Retenido', copy=False)
    numero_factura = fields.Char(string='Número de Factura', copy=False)
    numero_control = fields.Char(string='Número de Control', copy=False)
    numero_control_unico = fields.Char(string='Número de Control Unico', copy=False)
    fecha_operacion = fields.Date(string='Fecha de Operación', copy=False)
    codigo_concepto = fields.Char(string='Código del Concepto', copy=False)
    monto_operacion = fields.Char(string='Monto de Operación', copy=False)
    porcentaje_retencion = fields.Char(string='Porcentaje de Retención', copy=False)
