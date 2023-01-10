# -*- coding: utf-8 -*-

from odoo import fields, models
from datetime import datetime
import base64
import xlwt
import logging
_logger = logging.getLogger(__name__)


class AccountBookPurchase(models.Model):
    _name = 'account.book.purchase'
    _description = 'Book Purchase'
    _rec_name = 'id'

    f_inicio = fields.Date("Fecha de inicio", required=True, copy=False)
    f_fin = fields.Date("Fecha final", required=True, copy=False)

    # No gravadas
    no_grabadas_base = fields.Float("Total base compras no gravadas", readonly=True, copy=False)
    no_grabadas_cred = fields.Float("Total crédito fiscal compras no gravadas", readonly=True, copy=False)
    no_grabadas_ret = fields.Float("Total I.V.A retenido compras no gravadas", readonly=True, copy=False)

    # Importación
    imp_alic_gen_base = fields.Float("Total base compras importaciones gravadas con alicuota general", readonly=True,
                                     copy=False)
    imp_alic_gen_cred = fields.Float("Total crédito fiscal compras importaciones gravadas con alicuota general",
                                     readonly=True, copy=False)
    imp_alic_gen_ret = fields.Float("Total I.V.A retenido compras importaciones gravadas con alicuota general",
                                    readonly=True, copy=False)

    imp_alic_gen_add_base = fields.Float("Total base compras importaciones gravadas con alicuota general más adicional",
                                         readonly=True, copy=False)
    imp_alic_gen_add_cred = fields.Float(
        "Total crédito fiscal compras importaciones gravadas con alicuota general más adicional", readonly=True,
        copy=False)
    imp_alic_gen_add_ret = fields.Float(
        "Total I.V.A retenido compras importaciones gravadas con alicuota general más adicional", readonly=True,
        copy=False)

    imp_alic_red_base = fields.Float("Total base compras importaciones gravadas con alicuota reducida", readonly=True,
                                     copy=False)
    imp_alic_red_cred = fields.Float("Total crédito fiscal compras importaciones gravadas con alicuota reducida",
                                     readonly=True, copy=False)
    imp_alic_red_ret = fields.Float("Total I.V.A retenido compras importaciones gravadas con alicuota reducida",
                                    readonly=True, copy=False)

    # Internas
    int_alic_gen_base = fields.Float("Total base compras internas gravadas solo alicuota general", readonly=True,
                                     copy=False)
    int_alic_gen_cred = fields.Float("Total crédito fiscal compras internas gravadas solo alicuota general",
                                     readonly=True, copy=False)
    int_alic_gen_ret = fields.Float("Total I.V.A retenido compras internas gravadas solo alicuota general",
                                    readonly=True, copy=False)

    int_alic_gen_add_base = fields.Float("Total base compras internas gravadas solo alicuota general mas adicional",
                                         readonly=True, copy=False)
    int_alic_gen_add_cred = fields.Float(
        "Total crédito fiscal compras internas gravadas solo alicuota general mas adicional", readonly=True, copy=False)
    int_alic_gen_add_ret = fields.Float(
        "Total I.V.A retenido compras internas gravadas solo alicuota general mas adicional", readonly=True, copy=False)

    int_alic_red_base = fields.Float("Total base compras internas gravadas solo alicuota reducida", readonly=True,
                                     copy=False)
    int_alic_red_cred = fields.Float("Total crédito fiscal compras internas gravadas solo alicuota reducida",
                                     readonly=True, copy=False)
    int_alic_red_ret = fields.Float("Total I.V.A retenido compras internas gravadas solo alicuota reducida",
                                    readonly=True, copy=False)

    # Lineas
    line_ids = fields.One2many('account.book.purchase.line', 'account_book_purchase_id', string='Lineas', copy=False)
    company_id = fields.Many2one(comodel_name='res.company', string='Compañía', default=lambda x: x.env.company.id,
                                 copy=False)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('generate', 'Libro Generado'),
        ('file_generate', 'Archivo Generado')],
        default='draft')
    attachment_ids = fields.Many2many(string='Attachments', comodel_name='ir.attachment',
                                      relation='account_book_purchase_rel', column1='account_book_purchase_id',
                                      column2='attachment_id', copy=False)

    def update_book_purchase(self):
        line = []
        self.no_grabadas_base = 0.0
        self.no_grabadas_cred = 0.0
        self.no_grabadas_ret = 0.0
        self.imp_alic_gen_base = 0.0
        self.imp_alic_gen_cred = 0.0
        self.imp_alic_gen_ret = 0.0
        self.imp_alic_gen_add_base = 0.0
        self.imp_alic_gen_add_cred = 0.0
        self.imp_alic_gen_add_ret = 0.0
        self.imp_alic_red_base = 0.0
        self.imp_alic_red_cred = 0.0
        self.imp_alic_red_ret = 0.0
        self.int_alic_gen_base = 0.0
        self.int_alic_gen_cred = 0.0
        self.int_alic_gen_ret = 0.0
        self.int_alic_gen_add_base = 0.0
        self.int_alic_gen_add_cred = 0.0
        self.int_alic_gen_add_ret = 0.0
        self.int_alic_red_base = 0.0
        self.int_alic_red_cred = 0.0
        self.int_alic_red_ret = 0.0
        self.line_ids.unlink()
        desde = fields.Date.from_string(self.f_inicio)
        hasta = fields.Date.from_string(self.f_fin)
        query = """
            SELECT
                move.id,
                move.date,
                move.move_type,
                move.import_form_num,
                move.import_dossier,
                move.import_date,
                move.amount_untaxed,
                move.iva_general,
                move.iva_reduced,
                move.iva_exempt,
                move.invoice_date,
                move.ref,
                move.reason,
                move.debit_origin_id,
                move.invoice_number_next,
                move.invoice_number_control,
                move.invoice_number_unique,
                move.amount_total,
                move.hide_book,
                partner.taxpayer,
                partner.name,
                partner.vat,
                partner.people_type,
                ret_iva.iva_date,
                ret_iva.amount_total_retention,
                ret_iva.name AS name_ret
                FROM account_move AS move
                INNER JOIN res_partner AS partner
                ON partner.id = move.partner_id
                LEFT JOIN retention_iva AS ret_iva
                ON move.id = ret_iva.move_id
                WHERE move.date BETWEEN '%s' AND '%s'
                AND move.state = 'posted'
                AND move.move_type in ('in_invoice', 'in_refund', 'in_receipt')
                AND move.hide_book is False
                ORDER BY move.date
        """ % (desde, hasta)
        self._cr.execute(query)
        obj_query = self._cr.dictfetchall()
        for book in obj_query:
            compra_imp_base = 0.0
            compra_imp_porcent = ''
            compra_imp_importe = 0.0
            compra_int_base = 0.0
            compra_int_porcent = ''
            compra_int_importe = 0.0
            compra_int_base_r = 0.0
            compra_int_porcent_r = ''
            compra_int_importe_r = 0.0
            doc_type = ''
            doc_af = ''
            people_type = ''

            if book['move_type'] == 'in_invoice' and not book['debit_origin_id']:
                doc_type += '1'
            if book['move_type'] == 'in_invoice' and book['debit_origin_id']:
                doc_type += '2'
                doc_af += book['reason']
            if book['move_type'] == 'in_refund':
                doc_type += '3'
                doc_af += book['reason']

            if book['people_type'] == 'na':
                people_type += 'N/A'

            if book['people_type'] == 'resident_nat_people':
                people_type += 'PNRE'

            if book['people_type'] == 'non_resit_nat_people':
                people_type += 'PNNR'

            if book['people_type'] == 'domi_ledal_entity':
                people_type += 'PJDO'

            if book['people_type'] == 'legal_ent_not_domicilied':
                people_type += 'PJDO'

            if book['iva_general'] > 0.0:
                if book['import_form_num'] or book['import_dossier'] or book['import_date']:
                    compra_imp_base += book['amount_untaxed']
                    compra_imp_porcent += '16'
                    compra_imp_importe += book['iva_general']
                else:
                    compra_int_base += book['amount_untaxed']
                    compra_int_porcent += '16'
                    compra_int_importe += book['iva_general']
            if book['iva_exempt'] > 0.0:
                compra_int_base += book['amount_untaxed']
                compra_int_importe += 0.0

            if book['iva_reduced'] > 0.0:
                compra_int_base_r = book['amount_untaxed']
                compra_int_porcent_r = '8'
                compra_int_importe_r = book['iva_reduced']

            line.append((0, 0, {
                'date': book['invoice_date'],
                'doc_type': doc_type,
                'numero_factura': book['invoice_number_next'],
                'control': book['invoice_number_control'] if book['invoice_number_control']
                else book['invoice_number_unique'] or '',
                'nota_deb':  book['invoice_number_next'] if book['move_type'] == 'in_refund' else '',
                'nota_cred': book['invoice_number_next'] if book['move_type'] == 'in_invoice'
                and book['debit_origin_id'] else '',
                'doc_afectado': doc_af,
                'nombre_social': book['name'],
                'rif': book['vat'],
                'total_compras': book['amount_total'],
                'compras_sin_credito': book['iva_exempt'],
                'compra_imp_base': compra_imp_base,
                'compra_imp_porcent': compra_imp_porcent,
                'compra_imp_importe': compra_imp_importe,
                'compra_int_base': compra_int_base,
                'compra_int_porcent': compra_int_porcent,
                'compra_int_importe': compra_int_importe,
                'compra_int_base_r': compra_int_base_r,
                'compra_int_porcent_r': compra_int_porcent_r,
                'compra_int_importe_r': compra_int_importe_r,
                'iva_retenido': book['amount_total_retention'],
                'comprobante': book['name_ret'],
                'periodos': 0,
                'iva_date': book['iva_date'],
                'people_type': people_type,
                'account_book_purchase_id': self.id,
            }))
        self.write({'line_ids': line, 'state': 'generate'})
        self.update_book_tax()

    def update_book_tax(self):
        no_grabadas_base = 0.0
        no_grabadas_cred = 0.0
        no_grabadas_ret = 0.0
        imp_alic_gen_base = 0.0
        imp_alic_gen_cred = 0.0
        imp_alic_gen_ret = 0.0
        imp_alic_gen_add_base = 0.0
        imp_alic_gen_add_cred = 0.0
        imp_alic_gen_add_ret = 0.0
        imp_alic_red_base = 0.0
        imp_alic_red_cred = 0.0
        imp_alic_red_ret = 0.0
        int_alic_gen_base = 0.0
        int_alic_gen_cred = 0.0
        int_alic_gen_ret = 0.0
        int_alic_gen_add_base = 0.0
        int_alic_gen_add_cred = 0.0
        int_alic_gen_add_ret = 0.0
        int_alic_red_base = 0.0
        int_alic_red_cred = 0.0
        int_alic_red_ret = 0.0
        for line_inv in self.line_ids.filtered(lambda x: x.doc_type in ('1', '3')):
            if line_inv.compras_sin_credito > 0.0:
                no_grabadas_base += line_inv.compra_int_base
                no_grabadas_cred += line_inv.compra_int_importe
                no_grabadas_ret += line_inv.compra_int_importe_r

            if line_inv.compra_int_porcent == '16':
                int_alic_gen_base += line_inv.compra_int_base
                int_alic_gen_cred += line_inv.compra_int_importe
                int_alic_gen_ret += line_inv.iva_retenido

            if line_inv.compra_int_porcent == '8':
                int_alic_red_base += line_inv.compra_int_base
                int_alic_red_cred += line_inv.compra_int_importe
                int_alic_red_ret += line_inv.iva_retenido

            if line_inv.compra_int_porcent == '24':
                int_alic_gen_add_base += line_inv.compra_int_base
                int_alic_gen_add_cred += line_inv.compra_int_importe
                int_alic_gen_add_ret += line_inv.iva_retenido

            if line_inv.compra_imp_importe > 0.0 or line_inv.compra_imp_base > 0.0:

                if line_inv.compra_int_porcent == '16':
                    imp_alic_gen_base += line_inv.compra_int_base
                    imp_alic_gen_cred += line_inv.compra_int_importe
                    imp_alic_gen_ret += line_inv.iva_retenido

                if line_inv.compra_int_porcent == '8':
                    imp_alic_red_base += line_inv.compra_int_base
                    imp_alic_red_cred += line_inv.compra_int_importe
                    imp_alic_red_ret += line_inv.iva_retenido

                if line_inv.compra_int_porcent == '24':
                    imp_alic_gen_add_base += line_inv.compra_int_base
                    imp_alic_gen_add_cred += line_inv.compra_int_importe
                    imp_alic_gen_add_ret += line_inv.iva_retenido
        self.update_book_tax_debit(no_grabadas_base, no_grabadas_cred, no_grabadas_ret, imp_alic_gen_base,
                                   imp_alic_gen_cred, imp_alic_gen_ret, imp_alic_gen_add_base, imp_alic_gen_add_cred,
                                   imp_alic_gen_add_ret, imp_alic_red_base, imp_alic_red_cred, imp_alic_red_ret,
                                   int_alic_gen_base, int_alic_gen_cred, int_alic_gen_ret, int_alic_gen_add_base,
                                   int_alic_gen_add_cred, int_alic_gen_add_ret, int_alic_red_base, int_alic_red_cred,
                                   int_alic_red_ret)

    def update_book_tax_debit(self, no_grabadas_base, no_grabadas_cred, no_grabadas_ret, imp_alic_gen_base,
                              imp_alic_gen_cred, imp_alic_gen_ret, imp_alic_gen_add_base, imp_alic_gen_add_cred,
                              imp_alic_gen_add_ret, imp_alic_red_base, imp_alic_red_cred, imp_alic_red_ret,
                              int_alic_gen_base, int_alic_gen_cred, int_alic_gen_ret, int_alic_gen_add_base,
                              int_alic_gen_add_cred, int_alic_gen_add_ret, int_alic_red_base, int_alic_red_cred,
                              int_alic_red_ret):

        no_grabadas_base_d = 0.0
        no_grabadas_cred_d = 0.0
        no_grabadas_ret_d = 0.0
        imp_alic_gen_base_d = 0.0
        imp_alic_gen_cred_d = 0.0
        imp_alic_gen_ret_d = 0.0
        imp_alic_gen_add_base_d = 0.0
        imp_alic_gen_add_cred_d = 0.0
        imp_alic_gen_add_ret_d = 0.0
        imp_alic_red_base_d = 0.0
        imp_alic_red_cred_d = 0.0
        imp_alic_red_ret_d = 0.0
        int_alic_gen_base_d = 0.0
        int_alic_gen_cred_d = 0.0
        int_alic_gen_ret_d = 0.0
        int_alic_gen_add_base_d = 0.0
        int_alic_gen_add_cred_d = 0.0
        int_alic_gen_add_ret_d = 0.0
        int_alic_red_base_d = 0.0
        int_alic_red_cred_d = 0.0
        int_alic_red_ret_d = 0.0

        for line_inv in self.line_ids.filtered(lambda x: x.doc_type == '2'):
            if line_inv.compras_sin_credito > 0.0:
                no_grabadas_base_d += line_inv.compra_int_base
                no_grabadas_cred_d += line_inv.compra_int_importe
                no_grabadas_ret_d += line_inv.compra_int_importe_r

            if line_inv.compra_int_porcent == '16':
                int_alic_gen_base_d += line_inv.compra_int_base
                int_alic_gen_cred_d += line_inv.compra_int_importe
                int_alic_gen_ret_d += line_inv.iva_retenido

            if line_inv.compra_int_porcent == '8':
                int_alic_red_base_d += line_inv.compra_int_base
                int_alic_red_cred_d += line_inv.compra_int_importe
                int_alic_red_ret_d += line_inv.iva_retenido

            if line_inv.compra_int_porcent == '24':
                int_alic_gen_add_base_d += line_inv.compra_int_base
                int_alic_gen_add_cred_d += line_inv.compra_int_importe
                int_alic_gen_add_ret_d += line_inv.iva_retenido

            if line_inv.compra_imp_importe > 0.0 or line_inv.compra_imp_base > 0.0:

                if line_inv.compra_int_porcent == '16':
                    imp_alic_gen_base_d += line_inv.compra_int_base
                    imp_alic_gen_cred_d += line_inv.compra_int_importe
                    imp_alic_gen_ret_d += line_inv.iva_retenido

                if line_inv.compra_int_porcent == '8':
                    imp_alic_red_base_d += line_inv.compra_int_base
                    imp_alic_red_cred_d += line_inv.compra_int_importe
                    imp_alic_red_ret_d += line_inv.iva_retenido

                if line_inv.compra_int_porcent == '24':
                    imp_alic_gen_add_base_d += line_inv.compra_int_base
                    imp_alic_gen_add_cred_d += line_inv.compra_int_importe
                    imp_alic_gen_add_ret_d += line_inv.iva_retenido

        self.no_grabadas_base = no_grabadas_base - no_grabadas_base_d
        self.no_grabadas_cred = no_grabadas_cred - no_grabadas_cred_d
        self.no_grabadas_ret = no_grabadas_ret - no_grabadas_ret_d
        self.imp_alic_gen_base = imp_alic_gen_base - imp_alic_gen_base_d
        self.imp_alic_gen_cred = imp_alic_gen_cred - imp_alic_gen_cred_d
        self.imp_alic_gen_ret = imp_alic_gen_ret - imp_alic_gen_ret_d
        self.imp_alic_gen_add_base = imp_alic_gen_add_base - imp_alic_gen_add_base_d
        self.imp_alic_gen_add_cred = imp_alic_gen_add_cred - imp_alic_gen_add_cred_d
        self.imp_alic_gen_add_ret = imp_alic_gen_add_ret - imp_alic_gen_add_ret_d
        self.imp_alic_red_base = imp_alic_red_base - imp_alic_red_base_d
        self.imp_alic_red_cred = imp_alic_red_cred - imp_alic_red_cred_d
        self.imp_alic_red_ret = imp_alic_red_ret - imp_alic_red_ret_d
        self.int_alic_gen_base = int_alic_gen_base - int_alic_gen_base_d
        self.int_alic_gen_cred = int_alic_gen_cred - int_alic_gen_cred_d
        self.int_alic_gen_ret = int_alic_gen_ret - int_alic_gen_ret_d
        self.int_alic_gen_add_base = int_alic_gen_add_base - int_alic_gen_add_base_d
        self.int_alic_gen_add_cred = int_alic_gen_add_cred - int_alic_gen_add_cred_d
        self.int_alic_gen_add_ret = int_alic_gen_add_ret - int_alic_gen_add_ret_d
        self.int_alic_red_base = int_alic_red_base - int_alic_red_base_d
        self.int_alic_red_cred = int_alic_red_cred - int_alic_red_cred_d
        self.int_alic_red_ret = int_alic_red_ret - int_alic_red_ret_d

    def generate_xlsx(self):
        start_time = datetime.now()
        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('Resumen Libro de Compras')

        bold_font = xlwt.easyxf(
            "font:bold 1, height 250; borders: top dashed, bottom dashed, left dashed, right dashed;")
        total_title = xlwt.easyxf(
            "font:bold 1, height 200; borders: top dashed, bottom dashed, left dashed, right dashed;")
        bold_center = xlwt.easyxf(
            "font:bold 1, height 250; align: horiz center; borders: top dashed, bottom dashed,"
            "left dashed, right dashed; align:vert center;")
        head_style = xlwt.easyxf(
            "font: bold 1; align:horiz center; align:vert center; alignment: wrap True;"
            "borders: top dashed, bottom dashed, left dashed, right dashed;")
        reduce_head = xlwt.easyxf(
            "font: bold 1;font: height 170; align:horiz center; align:vert center; alignment: wrap True;"
            "borders: top dashed, bottom dashed, left dashed, right dashed;")
        value_style = xlwt.easyxf(
            "align: horiz right; font:height 180; borders: bottom dashed,left dashed,right dashed")
        value_style_l = xlwt.easyxf(
            "align: horiz left; font:height 180; borders: bottom dashed,left dashed,right dashed")
        total_style = xlwt.easyxf(
            "align: horiz right; font:height 180; borders:top dashed, bottom dashed,left dashed,right dashed")
        calc_style = xlwt.easyxf(
            "align: horiz left; borders: bottom dashed, bottom_color white,left dashed,"
            "left_color white,right dashed, right_color white")
        calc_style_r = xlwt.easyxf(
            "align: horiz right; borders: bottom dashed, bottom_color white, left dashed,"
            "left_color white,right dashed, right_color white")

        if self.company_id.vat:
            vat = self.company_id.vat
        else:
            vat = ''
        ws.write_merge(0, 0, 0, 13, "EMPRESA: " + self.company_id.name.upper(), bold_font)
        ws.write_merge(0, 0, 14, 27, "RIF:" + vat, bold_font)
        ws.write_merge(1, 1, 0, 16, "LIBRO DE COMPRAS", bold_center)
        ws.write_merge(1, 1, 17, 27, " ", bold_center)
        ws.write_merge(2, 2, 0, 16, "COMPRAS CORRESPONDIENTES DEL " + self.f_inicio.strftime(
            '%d/%m/%Y') + " AL " + self.f_fin.strftime('%d/%m/%Y'), bold_center)
        ws.write_merge(2, 2, 17, 27, " ", bold_center)

        head = [
            "#", "Fecha del Documento", "Tipo\nDoc.", "Nombre/R.Social", "CI/ RIF", "Tipo de Persona", "Fact Nº",
            "Nº Control", "Nota de\nDébito Nº", "Nota de\nCrédito Nº", "Documento\nafectado Nº",
            "NUmero de Planilla\nde importación", "Numero Expediente\n Importaciones","Fecha de Importaciones",
            "Total compras\n(incluye iva)", "Compras sin derecho a credito",
        ]

        row = 3
        col = 0

        for index, item in enumerate(head):
            if index != 5:
                ws.write_merge(row, row + 4, col, col, item, head_style)
            else:
                ws.write_merge(row, row + 4, col, col, item, reduce_head)
            col += 1

        ws.write_merge(3, 3, 16, 24, "Compras con derecho a credito", head_style)
        ws.write_merge(4, 5, 16, 18, "Compras de importación", head_style)
        ws.write_merge(4, 5, 19, 21, "Compras internas", head_style)
        ws.write_merge(4, 5, 22, 24, "Compras internas alicuota reducida", head_style)
        head = ["Base", "%", "Crédito fiscal"]
        row = 6
        col = 16

        for x in range(3):
            for item in head:
                ws.write_merge(row, row + 1, col, col, item, head_style)
                col += 1

        row = 3
        col = 25

        head = ["I.V.A retenido", "Nº. de comprobante", "Fecha Compr.", "N/C ó N/D de periodos anteriores a ajustar"]

        for item in head:
            ws.write_merge(row, row + 4, col, col, item, head_style)
            col += 1

        row = 8
        col = 0

        total_compras = 0.0
        total_sin_credito = 0.0
        total_base_importacion = 0.0
        total_iva_importacion = 0.0
        total_base_internas = 0.0
        total_iva_internas = 0.0
        total_base_internas_r = 0.0
        total_iva_internas_r = 0.0
        total_iva_ret = 0.0
        total_periodos = 0.0

        for item in self.line_ids.filtered(lambda x: x.doc_type in ('1', '3')):
            total_compras += item.total_compras
            total_sin_credito += item.compras_sin_credito
            total_base_importacion += item.compra_imp_base
            total_iva_importacion += item.compra_imp_importe
            total_base_internas += 0.0 if item.compras_sin_credito else item.compra_int_base
            total_iva_internas += item.compra_int_importe
            total_base_internas_r += item.compra_int_base_r
            total_iva_internas_r += item.compra_int_importe_r
            total_iva_ret += item.iva_retenido
            total_periodos += item.periodos

        for item in self.line_ids.filtered(lambda x: x.doc_type == '2'):
            total_compras -=  item.total_compras
            total_sin_credito -= item.compras_sin_credito
            total_base_importacion -= item.compra_imp_base
            total_iva_importacion -= item.compra_imp_importe
            total_base_internas -= item.compra_int_base
            total_iva_internas -= item.compra_int_importe
            total_base_internas_r -= item.compra_int_base_r
            total_iva_internas_r -= item.compra_int_importe_r
            total_iva_ret -= item.iva_retenido
            total_periodos -= item.periodos

        contador = 0
        for item in self.line_ids:
            contador += 1
            
            ws.write(row, col + 0, contador, value_style)
            ws.write(row, col + 1, item.date.strftime('%d/%m/%Y'), value_style_l)
            ws.write(row, col + 2, item.doc_type, value_style_l)
            ws.write(row, col + 3, item.nombre_social, value_style_l)
            ws.write(row, col + 4, item.rif, value_style_l)
            ws.write(row, col + 5, item.people_type, value_style_l)
            ws.write(row, col + 6,  '' if item.doc_afectado else item.numero_factura, value_style_l)
            ws.write(row, col + 7, item.control, value_style_l)
            ws.write(row, col + 8, item.nota_cred, value_style_l)
            ws.write(row, col + 9, item.nota_deb, value_style_l)
            ws.write(row, col + 10, item.doc_afectado, value_style_l)
            ws.write(row, col + 11, '', value_style_l)
            ws.write(row, col + 12, '', value_style_l)
            ws.write(row, col + 13, '', value_style_l)
            ws.write(row, col + 14, item.total_compras, value_style)
            ws.write(row, col + 15, item.compras_sin_credito, value_style)

            ws.write(row, col + 16, item.compra_imp_base, value_style)
            ws.write(row, col + 17, item.compra_imp_porcent if item.compra_imp_porcent else "0.0", value_style)
            ws.write(row, col + 18, item.compra_imp_importe, value_style)

            ws.write(row, col + 19, "0.0" if item.compras_sin_credito else item.compra_int_base, value_style)
            ws.write(row, col + 20, item.compra_int_porcent if item.compra_int_porcent else "0.0", value_style)
            ws.write(row, col + 21, item.compra_int_importe, value_style)

            ws.write(row, col + 22, item.compra_int_base_r, value_style)
            ws.write(row, col + 23, item.compra_int_porcent_r if item.compra_int_porcent_r else "0.0", value_style)
            ws.write(row, col + 24, item.compra_int_importe_r, value_style)

            ws.write(row, col + 25, item.iva_retenido, value_style)
            ws.write(row, col + 26, item.comprobante if item.comprobante else '', value_style_l)
            ws.write(row, col + 27, item.iva_date.strftime('%d/%m/%Y') if item.iva_date else "", value_style_l)
            ws.write(row, col + 28, item.periodos, value_style)

            row += 1
        col = 0

        ws.write_merge(row, row, col, col + 13, "Totales afectos a tasa  general", total_title)

        ws.write(row, 14, total_compras, total_style)
        ws.write(row, 15, total_sin_credito, total_style)
        ws.write(row, 16, total_base_importacion, total_style)
        ws.write(row, 17, " ", total_style)
        ws.write(row, 18, total_iva_importacion, total_style)
        ws.write(row, 19, total_base_internas, total_style)
        ws.write(row, 20, " ", total_style)
        ws.write(row, 21, total_iva_internas, total_style)
        ws.write(row, 22, " ", total_style)
        ws.write(row, 23, " ", total_style)
        ws.write(row, 24, " ", total_style)
        ws.write(row, 25, total_iva_ret, total_style)
        ws.write(row, 26, " ", total_style)
        ws.write(row, 27, " ", total_style)
        row += 1

        ws.write_merge(row, row, col, col + 9, "Totales afectos a tasa  reducida", total_title)
        ws.write_merge(row, row, 10, 21, " ", total_style)
        ws.write(row, 22, total_base_internas_r, total_style)
        ws.write(row, 23, " ", total_style)
        ws.write(row, 24, total_iva_internas_r, total_style)
        ws.write_merge(row, row, 25, 27, " ", total_style)
        row += 1

        ws.write_merge(row, row, col, col + 9,
                        "Totales de N/C ó N/D de periodos anteriores en retenciones del mes a  ajustar", total_title)
        ws.write_merge(row, row, 10, 26, " ", total_style)
        ws.write(row, 27, total_periodos, total_style)

        row += 2
        ws.write_merge(row, row, 0, 5, "RESUMEN", head_style)
        col = 6
        head = ["Base imponible", "Crédito fiscal", "I.V.A retenido"]
        for item in head:
             ws.write_merge(row, row, col, col + 1, item, head_style)
             col += 2

        row += 1

        ws.write_merge(row, row, 0, 5, "Total compras no gravadas y/o sin derecho a credito", calc_style)
        ws.write_merge(row, row, 6, 7, self.no_grabadas_base, calc_style_r)
        ws.write_merge(row, row, 8, 9, self.no_grabadas_cred, calc_style_r)
        ws.write_merge(row, row, 10, 11, self.no_grabadas_ret, calc_style_r)

        row += 1

        ws.write_merge(row, row, 0, 5, "Total compras gravadas alicuota general", calc_style)
        ws.write_merge(row, row, 6, 7, self.imp_alic_gen_base, calc_style_r)
        ws.write_merge(row, row, 8, 9, self.imp_alic_gen_cred, calc_style_r)
        ws.write_merge(row, row, 10, 11, self.imp_alic_gen_ret, calc_style_r)

        row += 1

        ws.write_merge(row, row, 0, 5, "Total importaciones gravadas alicuota general mas adicional", calc_style)
        ws.write_merge(row, row, 6, 7, self.imp_alic_gen_add_base, calc_style_r)
        ws.write_merge(row, row, 8, 9, self.imp_alic_gen_add_cred, calc_style_r)
        ws.write_merge(row, row, 10, 11, self.imp_alic_gen_add_ret, calc_style_r)

        row += 1

        ws.write_merge(row, row, 0, 5, "Total importaciones gravadas por alicuota reducida", calc_style)
        ws.write_merge(row, row, 6, 7, self.imp_alic_red_base, calc_style_r)
        ws.write_merge(row, row, 8, 9, self.imp_alic_red_cred, calc_style_r)
        ws.write_merge(row, row, 10, 11, self.imp_alic_red_ret, calc_style_r)

        row += 1

        ws.write_merge(row, row, 0, 5, "Total compras gravadas alicuota general", calc_style)
        ws.write_merge(row, row, 6, 7, self.int_alic_gen_base, calc_style_r)
        ws.write_merge(row, row, 8, 9, self.int_alic_gen_cred, calc_style_r)
        ws.write_merge(row, row, 10, 11, self.int_alic_gen_ret, calc_style_r)

        row += 1

        ws.write_merge(row, row, 0, 5, "Total compras gravadas alicuota general mas adicional", calc_style)
        ws.write_merge(row, row, 6, 7, self.int_alic_gen_add_base, calc_style_r)
        ws.write_merge(row, row, 8, 9, self.int_alic_gen_add_cred, calc_style_r)
        ws.write_merge(row, row, 10, 11, self.int_alic_gen_add_ret, calc_style_r)

        row += 1

        ws.write_merge(row, row, 0, 5, "Total compras gravadas por alicuota reducida", calc_style)
        ws.write_merge(row, row, 6, 7, self.int_alic_red_base, calc_style_r)
        ws.write_merge(row, row, 8, 9, self.int_alic_red_cred, calc_style_r)
        ws.write_merge(row, row, 10, 11, self.int_alic_red_ret, calc_style_r)

        wb.save('/tmp/Libro de Compras.xls')
        file = open('/tmp/Libro de Compras.xls', 'rb')
        out = file.read()
        r = base64.b64encode(out)
        attachment = self.env['ir.attachment'].create({
            'name': 'Libro de Compra {0}-{1}.xls'.format(str(self.f_inicio), str(self.f_fin)),
            'res_id': self.id,
            'res_model': 'account.book.purchase',
            'datas': r,
            'type': 'binary',
        })
        self.write({'attachment_ids': attachment.ids, 'state': 'file_generate'})
        end_time = datetime.now()
        _logger.info(">> ({}) {}: {}  | {}: {}".format(
            'generate_xlsx',
            'Hora de Inicio', start_time,
            'Tiempo de ejecucion', end_time - start_time))
        return True


class AccountBookPurchaseLine(models.Model):
    _name = "account.book.purchase.line"
    _description = 'Book Line Purchase'
    _rec_name = 'id'

    date = fields.Date("Fecha")
    iva_date = fields.Date("Fecha retencion iva")
    people_type = fields.Char("Tipo de Persona")
    doc_type = fields.Selection(string='Tipo Documento', selection=[('1', 'Factura'),
                                                                    ('2', 'Nota de Débito'), ('3', 'Nota de Crédito')])
    numero_factura = fields.Char("Número de factura")
    nota_deb = fields.Char("Nota de débito")
    nota_cred = fields.Char("Nota de crédito")
    control = fields.Char("Número de control")
    doc_afectado = fields.Char("Documento afectado")
    nombre_social = fields.Char("Nombre /R. Social del proveedor")
    rif = fields.Char("RIF")
    total_compras = fields.Float("Total compras")
    compras_sin_credito = fields.Float("Compras sin derecho a credito")

    compra_imp_base = fields.Float("Base")
    compra_imp_porcent = fields.Selection([("8", "Alicuota reducida"), ("16", "Alicuota general"),
                                           ("24", "Alicuota más adicional")], string="Porcentaje de afecta",
                                          default="16")
    compra_imp_importe = fields.Float("Importe")

    compra_int_base = fields.Float("Base")
    compra_int_porcent = fields.Selection([("8", "Alicuota reducida"),
                                           ("16", "Alicuota general"), ("24", "Alicuota más adicional")],
                                          string="Porcentaje de afecta", default="16")
    compra_int_importe = fields.Float("Importe")

    compra_int_base_r = fields.Float("Base")
    compra_int_porcent_r = fields.Selection([("8", "Alicuota reducida")], string="Porcentaje de afecta", default="8")
    compra_int_importe_r = fields.Float("Importe")

    iva_retenido = fields.Float("I.V.A retenido")
    comprobante = fields.Char("Número de comprobante")
    periodos = fields.Float("NC o ND de periodos anteriores a ajustar")

    account_book_purchase_id = fields.Many2one('account.book.purchase', string='Libro')
