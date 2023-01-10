from odoo import fields, models
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class IslrXmlWizard(models.TransientModel):
    _name = 'islr.xml.wizard'
    _description = 'reporte xml islr'

    from_date = fields.Date(string='Date From', default=lambda *a: datetime.now().strftime('%Y-%m-%d'))
    to_date = fields.Date('Date To', default=lambda *a: (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'))

    def action_post_xml(self):
        lines = []
        start_time = datetime.now()
        desde = fields.Date.from_string(self.from_date)
        hasta = fields.Date.from_string(self.to_date)
        query =\
            """
                SELECT
                    partner.vat AS vat,
                    partner.doc_type AS doc_type,
                    ret.invoice_number_next AS numero_factura,
                    ret.invoice_number_control AS numero_control,
                    ret.invoice_number_unique AS numero_control_unico,
                    ret.isrl_date AS fehca_retencion,
                    ret_line.code AS code,
                    ret_line.base AS base,
                    ret_line.qty_retention AS qty_retention 
                FROM isrl_retention AS ret
                INNER JOIN isrl_retention_line AS ret_line
                ON ret.id = ret_line.retention_id
                INNER JOIN res_partner AS partner
                ON  partner.id = ret.partner_id
                WHERE ret.isrl_date BETWEEN '%s' AND '%s' AND ret.islr_type IN ('in_islr') AND ret.state IN ('done')
            """ % (desde, hasta)
        self._cr.execute(query)
        obj_query = self._cr.dictfetchall()
        vals = {
            'from_date': self.from_date,
            'to_date': self.to_date,
        }
        res = self.env['retention.xml.summary'].create(vals)
        for line in obj_query:
            lines.append((0, 0, {
                'sumary_retention_id': res.id,
                'rif_retenido': str(line['doc_type']) + '' + str(line['vat']) if len(line['vat']) == 6
                else str(line['doc_type']) + '' + str(line['vat']),
                'numero_factura': str(line['numero_factura']),
                'numero_control': str(line['numero_control']),
                'numero_control_unico': str(line['numero_control_unico']),
                'fecha_operacion': str(line['fehca_retencion']),
                'codigo_concepto': line['code'],
                'monto_operacion': str(line['base']),
                'porcentaje_retencion': str(line['qty_retention']),
            }))

        res.write({'line_ids': lines})

        action = self.env.ref('l10n_ve_isrl_retention.action_retention_xml_summary_new').read()[0]
        action['res_id'] = res.id
        end_time = datetime.now()
        _logger.info(">> ({}) {}: {}  | {}: {}".format(
            'action_post_xml',
            'Hora de Inicio', start_time,
            'Tiempo de ejecucion', end_time - start_time))
        return action


class WiizarXmlDescargar(models.TransientModel):
    _name = "islr.xml.download.wizard"

    name = fields.Char(string='Link', readonly="True")
    report = fields.Binary('Prepared file', readonly=True)
