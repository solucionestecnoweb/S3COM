from odoo import fields, models
from datetime import datetime, timedelta
import logging
import base64
_logger = logging.getLogger(__name__)


class RetentionIvaTxt(models.TransientModel):
    _name = 'retention.iva.txt.wizard'
    _description = 'Declaracion Iva TXT'

    from_date = fields.Date(string='Date From', default=lambda *a: datetime.now().strftime('%Y-%m-%d'))
    to_date = fields.Date('Date To', default=lambda *a: (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'))

    def action_post_txt(self):
        lines = []
        start_time = datetime.now()
        desde = fields.Date.from_string(self.from_date)
        hasta = fields.Date.from_string(self.to_date)
        query = """
        SELECT
            partner.name AS partner,
            partner.vat AS vat,
            partner.doc_type AS doc_type,
            ret_line.amount_tax AS importe,
            ret_line.amount_untaxed AS amount_untaxed,
            ret_line.amount_retention AS amount_retention,
            ret.invoice_number_next AS numero_factura,
            ret.invoice_number_control AS numero_control,
            ret.invoice_number_unique AS numero_control_unico,
            ret.ref AS ref,
            ret.debit_origin_id,
            ret.name AS ret_name,
            ret.iva_date AS iva_date,
            ret.move_date AS move_date,
            tax.amount AS amount_tax,
            tax.aliquot AS aliquot,
            ret.move_type AS move_type
            FROM retention_iva AS ret
            INNER JOIN retention_iva_line AS ret_line
            ON ret.id = ret_line.retention_iva_id
            INNER JOIN res_partner AS partner
            ON partner.id = ret.partner_id
            INNER JOIN account_tax_retention_iva_line_rel AS tax_rel
            ON ret_line.id = tax_rel.retention_iva_line_id
            INNER JOIN account_tax AS tax
            ON tax.id = tax_rel.account_tax_id
            WHERE ret.iva_date BETWEEN '%s' and '%s'
                AND ret.iva_type IN ('in_iva')
                AND ret.state IN ('done')
        """ % (desde, hasta)
        self._cr.execute(query)
        obj_query = self._cr.dictfetchall()
        file = open('/tmp/retencion_iva.txt', 'w')
        vals = {
            'from_date': self.from_date,
            'to_date': self.to_date,
            'state': 'generada',
        }
        res = self.env['retention.txt.summary'].create(vals)
        for line in obj_query:
            accum_exempt = 0.0
            if line['aliquot'] == 'exempt':
                accum_exempt += line['amount_untaxed']
            elif line['aliquot'] != 'exempt':
                file.write(self.env.company.doc_type + '' + self.env.company.vat + "\t")
                file.write(str(self.to_date.year) + '/' + str(self.to_date.month) + "\t")
                file.write(str(line['move_date']) + "\t")
                file.write("C" + "\t")
                if line['move_type'] == 'in_invoice':
                    file.write('01' + "\t")
                elif line['move_type'] == 'in_refund':
                    file.write('03' + "\t")
                elif line['move_type'] == 'in_invoice' and line['debit_origin_id']:
                    file.write('02' + "\t")
                file.write(line['doc_type'] + '' + line['vat'] + "\t")
                file.write(str(line['numero_factura']) + "\t")
                file.write(str(line['numero_control']) if line['numero_control']
                           else str(line['numero_control_unico']) + "\t")
                file.write('{:,.2f}'.format(line['amount_retention'] + line['amount_untaxed'] + accum_exempt)
                           + "\t")
                file.write('{:,.2f}'.format(line['amount_untaxed']) + "\t")
                file.write('{:,.2f}'.format(line['amount_retention']) + "\t")

                if not line['ref']:
                    file.write('0' + "\t")
                else:
                    file.write(line['ref'] + "\t")

                file.write(line['ret_name'] + "\t")
                file.write('{:,.2f}'.format(accum_exempt) + "\t")
                file.write(str(line['amount_tax']) + "\t")
                file.write('0' + "\n")

                if line['move_type'] == 'in_invoice':
                    lines.append((0, 0, {
                        'sumary_retention_txt_id': res.id,
                        'rif_retenido': line['doc_type'] + '' + line['vat'],
                        'numero_factura': line['numero_factura'],
                        'numero_control': line['numero_control'] if line['numero_control']
                        else line['numero_control_unico'],
                        'fecha_operacion': str(line['iva_date']),
                        'amount_retention': line['amount_retention'],
                        'amount_untaxed': str(line['amount_untaxed']),
                        'amount_tax': str(line['amount_tax']),
                        'codigo_concepto': '01',
                    }))
                if line['move_type'] == 'in_refund':
                    lines.append((0, 0, {
                        'sumary_retention_txt_id': res.id,
                        'rif_retenido': line['doc_type'] + '' + line['vat'],
                        'numero_factura': line['numero_factura'],
                        'numero_control': line['numero_control'] if line['numero_control']
                        else line['numero_control_unico'],
                        'fecha_operacion': str(line['iva_date']),
                        'amount_retention': line['amount_retention'],
                        'amount_untaxed': str(line['amount_untaxed']),
                        'amount_tax': str(line['amount_tax']),
                        'codigo_concepto': '03',
                    }))
                if line['move_type'] == 'in_receipt':
                    lines.append((0, 0, {
                        'sumary_retention_txt_id': res.id,
                        'rif_retenido': line['doc_type'] + '' + line['vat'],
                        'numero_factura': line['numero_factura'],
                        'numero_control': line['numero_control'] if line['numero_control']
                        else line['numero_control_unico'],
                        'fecha_operacion': str(line['iva_date']),
                        'amount_retention': line['amount_retention'],
                        'amount_untaxed': str(line['amount_untaxed']),
                        'amount_tax': str(line['amount_tax']),
                        'codigo_concepto': '02',
                    }))

        file.close()
        file = open('/tmp/retencion_iva.txt', 'rb')
        out = file.read()
        r = base64.b64encode(out)
        action = self.env.ref('l10n_ve_iva_retention.action_account_iva_download_wizard').read()[0]
        ids = self.env['iva.txt.download.wizard'].create({
             'report': r,
             'name': 'retencion_iva.txt'
        })

        attachment = self.env['ir.attachment'].create({
            'name': 'Resumen {0}-{1}.txt'.format(str(self.from_date), str(self.to_date)),
            'res_id': res.id,
            'res_model': 'retention.txt.summary',
            'datas': r,
            'type': 'binary',
        })

        res.write({'line_ids': lines, 'attachment_ids': attachment.ids})

        action['res_id'] = ids.id
        end_time = datetime.now()
        _logger.info(">> ({}) {}: {}  | {}: {}".format(
            'action_post_xml',
            'Hora de Inicio', start_time,
            'Tiempo de ejecucion', end_time - start_time))
        return action


class WiizarXmlDescargar(models.TransientModel):
    _name = "iva.txt.download.wizard"

    name = fields.Char(string='Link', readonly="True")
    report = fields.Binary('Prepared file', readonly=True)
