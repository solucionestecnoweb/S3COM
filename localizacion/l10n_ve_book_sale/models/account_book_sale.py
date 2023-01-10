# -*- coding: utf-8 -*-

from odoo import fields, models, api
from datetime import datetime
import base64
import xlwt
import logging
_logger = logging.getLogger(__name__)


class AccountBookSale(models.Model):
    _name = 'account.book.sale'
    _description = 'Book Sale'
    _rec_name = 'name'

    f_inicio = fields.Date("Fecha de inicio", required=True, copy=False)
    f_fin = fields.Date("Fecha final", required=True, copy=False)
    name = fields.Char(string='Numeracion', copy=False)
    # No gravadas
    no_grabadas_base = fields.Float("Total base ventas no gravadas", readonly=True, copy=False)
    no_grabadas_cred = fields.Float("Total débito fiscal ventas no gravadas", readonly=True, copy=False)
    no_grabadas_ret = fields.Float("Total I.V.A retenido ventas no gravadas", readonly=True, copy=False)

    # Exportación
    exp_alic_gen_base = fields.Float("Total base ventas exportaciones gravadas con alicuota general", readonly=True,
                                     copy=False)
    exp_alic_gen_cred = fields.Float("Total débito fiscal ventas exportaciones gravadas con alicuota general",
                                     readonly=True, copy=False)
    exp_alic_gen_ret = fields.Float("Total I.V.A retenido ventas exportaciones gravadas con alicuota general",
                                    readonly=True, copy=False)

    exp_alic_gen_add_base = fields.Float("Total base ventas exportaciones gravadas con alicuota general más adicional",
                                         readonly=True, copy=False)
    exp_alic_gen_add_cred = fields.Float(
        "Total débito fiscal ventas exportaciones gravadas con alicuota general más adicional", readonly=True,
        copy=False)
    exp_alic_gen_add_ret = fields.Float(
        "Total I.V.A retenido ventas exportaciones gravadas con alicuota general más adicional", readonly=True,
        copy=False)

    exp_alic_red_base = fields.Float("Total base ventas exportaciones gravadas con alicuota reducida", readonly=True,
                                     copy=False)
    exp_alic_red_cred = fields.Float("Total débito fiscal ventas exportaciones gravadas con alicuota reducida",
                                     readonly=True, copy=False)
    exp_alic_red_ret = fields.Float("Total I.V.A retenido ventas exportaciones gravadas con alicuota reducida",
                                    readonly=True, copy=False)

    # Internas
    int_alic_gen_base = fields.Float("Total base ventas internas gravadas solo alicuota general", readonly=True,
                                     copy=False)
    int_alic_gen_cred = fields.Float("Total débito fiscal ventas internas gravadas solo alicuota general",
                                     readonly=True, copy=False)
    int_alic_gen_ret = fields.Float("Total I.V.A retenido ventas internas gravadas solo alicuota general",
                                    readonly=True, copy=False)

    int_alic_gen_add_base = fields.Float("Total base ventas internas gravadas solo alicuota general mas adicional",
                                         readonly=True, copy=False)
    int_alic_gen_add_cred = fields.Float(
        "Total débito fiscal ventas internas gravadas solo alicuota general mas adicional", readonly=True, copy=False)
    int_alic_gen_add_ret = fields.Float(
        "Total I.V.A retenido ventas internas gravadas solo alicuota general mas adicional", readonly=True, copy=False)

    int_alic_red_base = fields.Float("Total base ventas internas gravadas solo alicuota reducida", readonly=True,
                                     copy=False)
    int_alic_red_cred = fields.Float("Total débito fiscal ventas internas gravadas solo alicuota reducida",
                                     readonly=True, copy=False)
    int_alic_red_ret = fields.Float("Total I.V.A retenido ventas internas gravadas solo alicuota reducida",
                                    readonly=True, copy=False)
    # Lineas
    line_ids = fields.One2many('account.book.sale.line', 'account_book_id', string='Lineas', readonly=True,
                               states={'draft': [('readonly', False)], 'generate': [('readonly', False)]}, copy=False)
    company_id = fields.Many2one(comodel_name='res.company', string='Compañía', default=lambda x: x.env.company.id,
                                 copy=False)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('generate', 'Libro Generado'),
        ('file_generate', 'Archivo Generado')],
        default='draft')
    attachment_ids = fields.Many2many(string='Attachments', comodel_name='ir.attachment',
                                      relation='account_book_rel', column1='account_book_id',
                                      column2='attachment_id', copy=False)

    @api.model
    def create(self, vals):
        res = super(AccountBookSale, self).create(vals)
        res.name = self.env['ir.sequence'].next_by_code('book.sale.sequence')
        return res

    def update_book_sale(self):
        line = []
        self.no_grabadas_base = 0.0
        self.no_grabadas_cred = 0.0
        self.no_grabadas_ret = 0.0
        self.exp_alic_gen_base = 0.0
        self.exp_alic_gen_cred = 0.0
        self.exp_alic_gen_ret = 0.0
        self.exp_alic_gen_add_base = 0.0
        self.exp_alic_gen_add_cred = 0.0
        self.exp_alic_gen_add_ret = 0.0
        self.exp_alic_red_base = 0.0
        self.exp_alic_red_cred = 0.0
        self.exp_alic_red_ret = 0.0
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
                move.iva_no_tax_credit,
                move.iva_exempt,
                move.invoice_date,
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
                ret_iva.amount_total_retention,
                ret_iva.name AS name_ret,
                ret_iva.iva_date
                FROM account_move AS move
                INNER JOIN res_partner AS partner
                ON partner.id = move.partner_id
                LEFT JOIN retention_iva AS ret_iva
                ON move.id = ret_iva.move_id
                WHERE move.date BETWEEN '%s' AND '%s'
                AND move.state = 'posted'
                AND move.move_type in ('out_invoice', 'out_refund', 'out_receipt')
                AND move.hide_book is False
                ORDER BY move.date
        """ % (desde, hasta)
        self._cr.execute(query)
        obj_query = self._cr.dictfetchall()
        for book in obj_query:
            venta_exp_base = 0.0
            venta_exp_porcent = 0.0
            venta_exp_importe = 0.0
            venta_int_base = 0.0
            venta_int_porcent = ''
            venta_int_importe = 0.0
            venta_int_base_r = 0.0
            venta_int_porcent_r = ''
            venta_int_importe_r = 0.0
            doc_type = ''
            doc_af = ''
            people_type = ''

            if book['move_type'] == 'out_invoice' and not book['debit_origin_id']:
                doc_type += '1'
            if book['move_type'] == 'out_invoice' and book['debit_origin_id']:
                doc_type += '2'
                doc_af += book['reason']
            if book['move_type'] == 'out_refund':
                doc_type += '3'
                doc_af += book['reason'] or ''

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
                    venta_exp_base += book['amount_untaxed']
                    venta_exp_porcent += '16'
                    venta_exp_importe += book['iva_general']
                    if book['taxpayer']:
                        venta_int_base += book['amount_untaxed']
                        venta_int_porcent += '16'
                        venta_int_importe += book['iva_general']
                if book['iva_exempt'] > 0.0:
                    venta_int_base += book['amount_untaxed']
                    venta_int_porcent += 0.0

                if book['iva_reduced'] > 0.0:
                    venta_int_base_r = book['amount_untaxed']
                    venta_int_porcent_r = '8'
                    venta_int_importe_r = book['iva_reduced']

            line.append((0, 0, {
                'date': book['invoice_date'],
                'doc_type': doc_type,
                'numero_factura': book['invoice_number_next'],
                'numero_z': book['invoice_number_control'] if book['invoice_number_control']
                else book['invoice_number_unique'] or '',
                'numero_mh': '',
                'nota_deb':  book['invoice_number_next'] if book['move_type'] == 'out_invoice'
                and book['debit_origin_id'] else '',
                'nota_cred': book['invoice_number_next'] if book['move_type'] == 'out_refund' else '',
                'doc_afectado': doc_af,
                'nombre_social': book['name'],
                'rif': book['vat'],
                'total_ventas': book['amount_total'],
                'ventas_sin_credito': book['iva_no_tax_credit'] + book['iva_exempt'],
                'venta_exp_base': venta_exp_base,
                'venta_exp_porcent': venta_exp_porcent,
                'venta_exp_importe': venta_exp_importe,
                'venta_int_base': venta_int_base,
                'venta_int_porcent': venta_int_porcent,
                'venta_int_importe': venta_int_importe,
                'venta_int_base_r': venta_int_base_r,
                'venta_int_porcent_r': venta_int_porcent_r,
                'venta_int_importe_r': venta_int_importe_r,
                'iva_retenido': book['amount_total_retention'],
                'comprobante': book['name_ret'],
                'periodos': 0,
                'iva_date': book['iva_date'],
                'people_type': people_type,
                'account_book_id': self.id,
            }))
        self.write({'line_ids': line, 'state': 'generate'})
        self.update_book_tax()

    def update_book_tax(self):
        no_grabadas_base = 0.0
        no_grabadas_cred = 0.0
        no_grabadas_ret = 0.0
        exp_alic_gen_base = 0.0
        exp_alic_gen_cred = 0.0
        exp_alic_gen_ret = 0.0
        exp_alic_gen_add_base = 0.0
        exp_alic_gen_add_cred = 0.0
        exp_alic_gen_add_ret = 0.0
        exp_alic_red_base = 0.0
        exp_alic_red_cred = 0.0
        exp_alic_red_ret = 0.0
        int_alic_gen_base = 0.0
        int_alic_gen_cred = 0.0
        int_alic_gen_ret = 0.0
        int_alic_gen_add_base = 0.0
        int_alic_gen_add_cred = 0.0
        int_alic_gen_add_ret = 0.0
        int_alic_red_base = 0.0
        int_alic_red_cred = 0.0
        int_alic_red_ret = 0.0
        for line_inv in self.line_ids.filtered(lambda x: x.doc_type in ('1', '2')):
            if line_inv.ventas_sin_credito > 0.0:
                no_grabadas_base += line_inv.venta_int_base
                no_grabadas_cred += line_inv.venta_int_importe
                no_grabadas_ret += line_inv.venta_int_importe_r

            if line_inv.venta_int_porcent == '16':
                int_alic_gen_base += line_inv.venta_int_base
                int_alic_gen_cred += line_inv.venta_int_importe
                int_alic_gen_ret += line_inv.iva_retenido

            if line_inv.venta_int_porcent == '8':
                int_alic_red_base += line_inv.venta_int_base
                int_alic_red_cred += line_inv.venta_int_importe
                int_alic_red_ret += line_inv.iva_retenido

            if line_inv.venta_int_porcent == '24':
                int_alic_gen_add_base += line_inv.venta_int_base
                int_alic_gen_add_cred += line_inv.venta_int_importe
                int_alic_gen_add_ret += line_inv.iva_retenido

            if line_inv.venta_exp_importe > 0.0 or line_inv.venta_exp_base > 0.0:

                if line_inv.venta_int_porcent == '16':
                    exp_alic_gen_base += line_inv.venta_int_base
                    exp_alic_gen_cred += line_inv.venta_int_importe
                    exp_alic_gen_ret += line_inv.iva_retenido

                if line_inv.venta_int_porcent == '8':
                    exp_alic_red_base += line_inv.venta_int_base
                    exp_alic_red_cred += line_inv.venta_int_importe
                    exp_alic_red_ret += line_inv.iva_retenido

                if line_inv.venta_int_porcent == '24':
                    exp_alic_gen_add_base += line_inv.venta_int_base
                    exp_alic_gen_add_cred += line_inv.venta_int_importe
                    exp_alic_gen_add_ret += line_inv.iva_retenido
        self.update_book_tax_credit(
            no_grabadas_base, no_grabadas_cred, no_grabadas_ret,
            exp_alic_gen_base, exp_alic_gen_cred, exp_alic_gen_ret,
            exp_alic_gen_add_base, exp_alic_gen_add_cred, exp_alic_gen_add_ret,
            exp_alic_red_base, exp_alic_red_cred, exp_alic_red_ret, int_alic_gen_base,
            int_alic_gen_cred, int_alic_gen_ret, int_alic_gen_add_base, int_alic_gen_add_cred,
            int_alic_gen_add_ret, int_alic_red_base, int_alic_red_cred, int_alic_red_ret)

    def update_book_tax_credit(self, no_grabadas_base, no_grabadas_cred, no_grabadas_ret,
                               exp_alic_gen_base, exp_alic_gen_cred, exp_alic_gen_ret,
                               exp_alic_gen_add_base, exp_alic_gen_add_cred, exp_alic_gen_add_ret,
                               exp_alic_red_base, exp_alic_red_cred, exp_alic_red_ret, int_alic_gen_base,
                               int_alic_gen_cred, int_alic_gen_ret, int_alic_gen_add_base, int_alic_gen_add_cred,
                               int_alic_gen_add_ret, int_alic_red_base, int_alic_red_cred, int_alic_red_ret):
    
        no_grabadas_base_c = 0.0
        no_grabadas_cred_c = 0.0
        no_grabadas_ret_c = 0.0
        exp_alic_gen_base_c = 0.0
        exp_alic_gen_cred_c = 0.0
        exp_alic_gen_ret_c = 0.0
        exp_alic_gen_add_base_c = 0.0
        exp_alic_gen_add_cred_c = 0.0
        exp_alic_gen_add_ret_c = 0.0
        exp_alic_red_base_c = 0.0
        exp_alic_red_cred_c = 0.0
        exp_alic_red_ret_c = 0.0
        int_alic_gen_base_c = 0.0
        int_alic_gen_cred_c = 0.0
        int_alic_gen_ret_c = 0.0
        int_alic_gen_add_base_c = 0.0
        int_alic_gen_add_cred_c = 0.0
        int_alic_gen_add_ret_c = 0.0
        int_alic_red_base_c = 0.0
        int_alic_red_cred_c = 0.0
        int_alic_red_ret_c = 0.0

        for line_inv in self.line_ids.filtered(lambda x: x.doc_type == '3'):
            if line_inv.ventas_sin_credito > 0.0:
                no_grabadas_base_c += line_inv.venta_int_base
                no_grabadas_cred_c += line_inv.venta_int_importe
                no_grabadas_ret_c += line_inv.venta_int_importe_r

            if line_inv.venta_int_porcent == '16':
                int_alic_gen_base_c += line_inv.venta_int_base
                int_alic_gen_cred_c += line_inv.venta_int_importe
                int_alic_gen_ret_c += line_inv.iva_retenido

            if line_inv.venta_int_porcent == '8':
                int_alic_red_base_c += line_inv.venta_int_base
                int_alic_red_cred_c += line_inv.venta_int_importe
                int_alic_red_ret_c += line_inv.iva_retenido

            if line_inv.venta_int_porcent == '24':
                int_alic_gen_add_base_c += line_inv.venta_int_base
                int_alic_gen_add_cred_c += line_inv.venta_int_importe
                int_alic_gen_add_ret_c += line_inv.iva_retenido

            if line_inv.venta_exp_importe > 0.0 or line_inv.venta_exp_base > 0.0:

                if line_inv.venta_int_porcent == '16':
                    exp_alic_gen_base_c += line_inv.venta_int_base
                    exp_alic_gen_cred_c += line_inv.venta_int_importe
                    exp_alic_gen_ret_c += line_inv.iva_retenido

                if line_inv.venta_int_porcent == '8':
                    exp_alic_red_base_c += line_inv.venta_int_base
                    exp_alic_red_cred_c += line_inv.venta_int_importe
                    exp_alic_red_ret_c += line_inv.iva_retenido

                if line_inv.venta_int_porcent == '24':
                    exp_alic_gen_add_base_c += line_inv.venta_int_base
                    exp_alic_gen_add_cred_c += line_inv.venta_int_importe
                    exp_alic_gen_add_ret_c += line_inv.iva_retenido

        self.no_grabadas_base = no_grabadas_base - no_grabadas_base_c
        self.no_grabadas_cred = no_grabadas_cred - no_grabadas_cred_c
        self.no_grabadas_ret = no_grabadas_ret - no_grabadas_ret_c
        self.exp_alic_gen_base = exp_alic_gen_base - exp_alic_gen_base_c
        self.exp_alic_gen_cred = exp_alic_gen_cred - exp_alic_gen_cred_c
        self.exp_alic_gen_ret = exp_alic_gen_ret - exp_alic_gen_ret_c
        self.exp_alic_gen_add_base = exp_alic_gen_add_base - exp_alic_gen_add_base_c
        self.exp_alic_gen_add_cred = exp_alic_gen_add_cred - exp_alic_gen_add_cred_c
        self.exp_alic_gen_add_ret = exp_alic_gen_add_ret - exp_alic_gen_add_ret_c
        self.exp_alic_red_base = exp_alic_red_base - exp_alic_red_base_c
        self.exp_alic_red_cred = exp_alic_red_cred - exp_alic_red_cred_c
        self.exp_alic_red_ret = exp_alic_red_ret - exp_alic_red_ret_c
        self.int_alic_gen_base = int_alic_gen_base - int_alic_gen_base_c
        self.int_alic_gen_cred = int_alic_gen_cred - int_alic_gen_cred_c
        self.int_alic_gen_ret = int_alic_gen_ret - int_alic_gen_ret_c
        self.int_alic_gen_add_base = int_alic_gen_add_base - int_alic_gen_add_base_c
        self.int_alic_gen_add_cred = int_alic_gen_add_cred - int_alic_gen_add_cred_c
        self.int_alic_gen_add_ret = int_alic_gen_add_ret - int_alic_gen_add_ret_c
        self.int_alic_red_base = int_alic_red_base - int_alic_red_base_c
        self.int_alic_red_cred = int_alic_red_cred - int_alic_red_cred_c
        self.int_alic_red_ret = int_alic_red_ret - int_alic_red_ret_c

    def generate_xlsx(self):
        start_time = datetime.now()
        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('Resumen Libro de Ventas')

        bold_font = xlwt.easyxf(
            "font:bold 1, height 250; borders: top dashed, bottom dashed, left dashed, right dashed;")
        total_title = xlwt.easyxf(
            "font:bold 1, height 200; borders: top dashed, bottom dashed, left dashed, right dashed;")
        bold_center = xlwt.easyxf(
            "font:bold 1, height 250; align: horiz center; borders: top dashed,"
            "bottom dashed, left dashed, right dashed; align:vert center;")
        head_style = xlwt.easyxf(
            "font: bold 1; align:horiz center; align:vert center; alignment: wrap True;"
            "borders: top dashed, bottom dashed, left dashed, right dashed;")
        reduce_head = xlwt.easyxf(
            "font: bold 1;font: height 170; align:horiz center; align:vert center;"
            "alignment: wrap True; borders: top dashed, bottom dashed, left dashed, right dashed;")
        value_style = xlwt.easyxf(
            "align: horiz right; font:height 180; borders: bottom dashed, left dashed, right dashed")
        value_style_l = xlwt.easyxf(
            "align: horiz left; font:height 180; borders: bottom dashed, left dashed, right dashed")
        total_style = xlwt.easyxf(
            "align: horiz right; font:height 180; borders:top dashed, bottom dashed,left dashed, right dashed")
        # result_line = xlwt.easyxf(
        #     "borders: bottom dashed, bottom_color white, left dashed, left_color white, right dashed")
        calc_style = xlwt.easyxf(
            "align: horiz left; borders: bottom dashed, bottom_color white, left dashed,"
            "left_color white,right dashed, right_color white")
        calc_style_r = xlwt.easyxf(
            "align: horiz right; borders: bottom dashed, bottom_color white,left dashed,"
            "left_color white,right dashed, right_color white")

        if self.company_id.vat:
            vat = self.company_id.vat
        else:
            vat = ''
        ws.write_merge(0, 0, 0, 13, "EMPRESA: " + self.company_id.name.upper(), bold_font)
        ws.write_merge(0, 0, 14, 27, "RIF:" + vat, bold_font)
        ws.write_merge(1, 1, 0, 16, "LIBRO DE VENTAS", bold_center)
        ws.write_merge(1, 1, 17, 27, " ", bold_center)
        ws.write_merge(2, 2, 0, 16, "VENTAS CORRESPONDIENTES DEL " + self.f_inicio.strftime(
            '%d/%m/%Y') + " AL " + self.f_fin.strftime('%d/%m/%Y'), bold_center)
        ws.write_merge(2, 2, 17, 27, " ", bold_center)

        head = [
            "#", "Fecha de Documento", "Tipo\nDoc.", "Nombre/R.Social del proveedor", "CI / RIF", "Tipo de Persona",
            "Numero de\nFactura Nº", "Numero de\nControl Nº", "Nota de\nDébito Nº", "Nota de\nCrédito Nº",
            "Documento\nafectado Nº", "Total ventas\n(incluye iva)", "Ventas exentas",
        ]

        row = 3
        col = 0

        for index, item in enumerate(head):
            if index != 5:
                ws.write_merge(row, row + 4, col, col, item, head_style)
            else:
                ws.write_merge(row, row + 4, col, col, item, reduce_head)
            col += 1

        ws.write_merge(3, 7, 13, 15, "Valor FOB total ventas de Exportación", head_style)
        ws.write_merge(3, 3, 16, 21, "Ventas Afectas (Débito Fiscal)", head_style)
        ws.write_merge(4, 5, 16, 18, "Ventas a Contribuyentes", head_style)
        ws.write_merge(4, 5, 19, 21, "Ventas a No Contribuyentes", head_style)

        head = ["Base", "%", "Débito fiscal"]
        row = 6
        col = 16

        for x in range(2):
            for item in head:
                ws.write_merge(row, row + 1, col, col, item, head_style)
                col += 1

        row = 3
        col = 22

        head = ["I.V.A retenido", "Nº. de comprobante",  "Fecha Compr.", "N/C ó N/D de periodos anteriores a ajustar"]

        for item in head:
            ws.write_merge(row, row + 4, col, col, item, head_style)
            col += 1

        row = 8
        col = 0

        total_ventas_a = 0.0
        total_sin_credito = 0.0
        total_base_exportacion = 0.0
        total_iva_exportacion = 0.0
        total_base_internas = 0.0
        total_iva_internas = 0.0
        total_base_internas_r = 0.0
        total_iva_internas_r = 0
        total_iva_ret = 0.0
        total_periodos = 0.0

        for item in self.line_ids.filtered(lambda x: x.doc_type in ('1', '2')):
            total_ventas_a += item.total_ventas
            total_sin_credito += item.ventas_sin_credito
            total_base_exportacion += item.venta_exp_base
            total_iva_exportacion += item.venta_exp_importe
            total_base_internas += 0.0 if item.ventas_sin_credito else item.venta_int_base
            total_iva_internas += item.venta_int_importe
            total_base_internas_r += item.venta_int_base_r
            total_iva_internas_r += item.venta_int_importe_r
            total_iva_ret += item.iva_retenido
            total_periodos += item.periodos

        for item in self.line_ids.filtered(lambda x: x.doc_type == '3'):
            total_ventas_a -= item.total_ventas
            total_sin_credito -= item.ventas_sin_credito
            total_base_exportacion -= item.venta_exp_base
            total_iva_exportacion -= item.venta_exp_importe
            total_base_internas -= item.venta_int_base
            total_iva_internas -= item.venta_int_importe
            total_base_internas_r -= item.venta_int_base_r
            total_iva_internas_r -= item.venta_int_importe_r
            total_iva_ret -= item.iva_retenido
            total_periodos -= item.periodos

        contador = 0
        for item in self.line_ids:
            contador += 1
            
            total_ventas = 0.0
            ventas_sin_credito = 0.0
            venta_int_base = 0.0
            venta_int_importe = 0.0
            venta_int_base_r = 0.0
            venta_int_importe_r = 0.0
            iva_retenido = 0.0
            
            total_ventas += item.total_ventas
            ventas_sin_credito += item.ventas_sin_credito
            venta_int_base += item.venta_int_base
            venta_int_importe += item.venta_int_importe
            venta_int_base_r += item.venta_int_base_r
            venta_int_importe_r += item.venta_int_importe_r
            iva_retenido += item.iva_retenido

            ws.write(row, col + 0, contador, value_style)
            ws.write(row, col + 1, item.date.strftime('%d/%m/%Y'), value_style_l)
            ws.write(row, col + 2, item.doc_type, value_style_l)
            ws.write(row, col + 3, item.nombre_social, value_style_l)
            ws.write(row, col + 4, item.rif, value_style_l)
            ws.write(row, col + 5, item.people_type, value_style_l)
            ws.write(row, col + 6, '' if item.doc_afectado else item.numero_factura, value_style_l)
            ws.write(row, col + 7, item.numero_z, value_style_l)
            ws.write(row, col + 8, item.nota_deb, value_style_l)
            ws.write(row, col + 9, item.nota_cred, value_style_l)
            ws.write(row, col + 10, item.doc_afectado, value_style_l)
            ws.write(row, col + 11, total_ventas, value_style)
            ws.write(row, col + 12, ventas_sin_credito, value_style)
            # ws.write(row, col + 4, item.numero_mh, value_style_l)

            ws.write_merge(row, row, col + 13, col + 15, item.venta_exp_base + item.venta_exp_importe, value_style)

            ws.write(row, col + 16, "0.0" if venta_int_base else ventas_sin_credito, value_style)
            ws.write(row, col + 17, item.venta_int_porcent if item.venta_int_porcent else '0,00', value_style)
            ws.write(row, col + 18, ventas_sin_credito, value_style)

            ws.write(row, col + 19, venta_int_base_r, value_style)
            ws.write(row, col + 20, item.venta_int_porcent_r if item.venta_int_porcent_r else '0,00', value_style)
            ws.write(row, col + 21, venta_int_importe_r, value_style)

            ws.write(row, col + 22, iva_retenido, value_style)
            ws.write(row, col + 23, item.comprobante, value_style_l)
            ws.write(row, col + 24, item.iva_date.strftime('%d/%m/%Y') if item.iva_date else "" , value_style_l)
            ws.write(row, col + 25, item.periodos, value_style)
            row += 1
        col = 0

        ws.write_merge(row, row, col, col + 10, "Totales afectos a tasa  general", total_title)
        ws.write(row, 11, total_ventas_a, total_style)
        ws.write(row, 12, total_sin_credito if total_sin_credito > 0.0 else 0, total_style)
        ws.write_merge(row, row, col + 13, col + 15, total_base_exportacion + total_iva_exportacion, total_style)
        ws.write(row, 16, total_base_internas, total_style)
        ws.write(row, 17, " ", total_style)
        ws.write(row, 18, total_iva_internas, total_style)
        ws.write(row, 19, " ", total_style)
        ws.write(row, 20, " ", total_style)
        ws.write(row, 21, " ", total_style)
        ws.write(row, 22, total_iva_ret, total_style)
        ws.write(row, 23, " ", total_style)
        ws.write(row, 24, " ", total_style)
        row += 1

        ws.write_merge(row, row, col, col + 10, "Totales afectos a tasa  reducida", total_title)
        ws.write_merge(row, row, 11, 18, " ", total_style)
        ws.write(row, 19, total_base_internas_r, total_style)
        ws.write(row, 20, " ", total_style)
        ws.write(row, 21, total_iva_internas_r, total_style)
        ws.write_merge(row, row, 22, 24, " ", total_style)

        row += 1

        ws.write_merge(row, row, col, col + 10,
                       "Totales de N/C ó N/D de periodos anteriores en retenciones del mes a  ajustar", total_title)
        ws.write_merge(row, row, 11, 23, " ", total_style)
        ws.write(row, 24, total_periodos, total_style)

        row += 2
        ws.write_merge(row, row, 0, 5, "RESUMEN", head_style)
        col = 6
        head = ["Base imponible", "Débito fiscal", "I.V.A retenido"]
        for item in head:
            ws.write_merge(row, row, col, col + 1, item, head_style)
            col += 2

        row += 1

        ws.write_merge(row, row, 0, 5, "Total ventas exentas o exoneradas", calc_style)
        ws.write_merge(row, row, 6, 7, self.no_grabadas_base, calc_style_r)
        ws.write_merge(row, row, 8, 9, self.no_grabadas_cred, calc_style_r)
        ws.write_merge(row, row, 10, 11, self.no_grabadas_ret, calc_style_r)

        row += 1

        ws.write_merge(row, row, 0, 5, "Total ventas gravadas alicuota general", calc_style)
        ws.write_merge(row, row, 6, 7, self.int_alic_gen_base), calc_style_r
        ws.write_merge(row, row, 8, 9, self.int_alic_gen_cred, calc_style_r)
        ws.write_merge(row, row, 10, 11, total_iva_ret), calc_style_r

        row += 1

        ws.write_merge(row, row, 0, 5, "Total ventas gravadas alicuota general mas adicional", calc_style)
        ws.write_merge(row, row, 6, 7, self.int_alic_gen_add_base, calc_style_r)
        ws.write_merge(row, row, 8, 9, self.int_alic_gen_add_cred, calc_style_r)
        ws.write_merge(row, row, 10, 11, self.int_alic_gen_add_ret, calc_style_r)

        row += 1

        ws.write_merge(row, row, 0, 5, "Total ventas gravadas por alicuota reducida", calc_style)
        ws.write_merge(row, row, 6, 7, self.int_alic_red_base, calc_style_r)
        ws.write_merge(row, row, 8, 9, self.int_alic_red_cred, calc_style_r)
        ws.write_merge(row, row, 10, 11, self.int_alic_red_ret, calc_style_r)

        row += 1

        ws.write_merge(row, row, 0, 5, "Total exportaciones", calc_style)
        ws.write_merge(row, row, 6, 7, self.exp_alic_gen_base + self.exp_alic_gen_add_base + self.exp_alic_red_base,
                       calc_style_r)
        ws.write_merge(row, row, 8, 9, self.exp_alic_gen_cred + self.exp_alic_gen_add_cred + self.exp_alic_red_cred,
                       calc_style_r)
        ws.write_merge(row, row, 10, 11, self.exp_alic_gen_ret + self.exp_alic_gen_add_ret + self.exp_alic_red_ret,
                       calc_style_r)

        row += 1

        ws.write_merge(row, row, 0, 5, "Total", calc_style)
        ws.write_merge(row, row, 6, 7,
                       self.exp_alic_gen_base +
                       self.exp_alic_gen_add_base +
                       self.exp_alic_red_base +
                       self.no_grabadas_base +
                       self.int_alic_gen_base +
                       self.int_alic_gen_add_base +
                       self.int_alic_red_base,
                       calc_style_r)
        ws.write_merge(row, row, 8, 9,
                       self.exp_alic_gen_cred +
                       self.exp_alic_gen_add_cred +
                       self.exp_alic_red_cred +
                       self.no_grabadas_cred +
                       self.int_alic_gen_cred +
                       self.int_alic_gen_add_cred +
                       self.int_alic_red_cred,
                       calc_style_r)
        ws.write_merge(row, row, 10, 11,
                       self.exp_alic_gen_ret +
                       self.exp_alic_gen_add_ret +
                       self.exp_alic_red_ret +
                       self.no_grabadas_ret +
                       self.int_alic_gen_ret +
                       self.int_alic_gen_add_ret +
                       self.int_alic_red_ret,
                       calc_style_r)

        wb.save('/tmp/Libro de Ventas.xls')
        file = open('/tmp/Libro de Ventas.xls', 'rb')
        out = file.read()
        r = base64.b64encode(out)
        attachment = self.env['ir.attachment'].create({
            'name': 'Resumen {0}-{1}.xls'.format(str(self.f_inicio), str(self.f_fin)),
            'res_id': self.id,
            'res_model': 'account.book.sale',
            'datas': r,
            'type': 'binary',
        })
        self.write({'attachment_ids': attachment.ids, 'state': 'file_generate'})
        end_time = datetime.now()
        _logger.info(">> ({}) {}: {}  | {}: {}".format(
            'action_post_xml',
            'Hora de Inicio', start_time,
            'Tiempo de ejecucion', end_time - start_time))
        return True


class AccountBookSaleLine(models.Model):
    _name = "account.book.sale.line"
    _description = 'Book Line Sale'
    _rec_name = 'id'

    date = fields.Date("Fecha")
    iva_date = fields.Date("Fecha retencion iva")
    doc_type = fields.Selection([('1', 'Factura'), ('2', 'Nota de Débito'), ('3', 'Nota de Crédito')],
                                string='Tipo Documento')
    numero_factura = fields.Char("Número de factura")
    people_type = fields.Char("Tipo de Persona")
    numero_z = fields.Char("Número Z")
    numero_mh = fields.Char("Número MH")
    nota_deb = fields.Char("Nota de débito")
    nota_cred = fields.Char("Nota de crédito")
    doc_afectado = fields.Char("Documento afectado")
    nombre_social = fields.Char("Nombre /R. Social del proveedor")
    rif = fields.Char("RIF")
    total_ventas = fields.Float("Total ventas")
    ventas_sin_credito = fields.Float("Ventas exentas")

    venta_exp_base = fields.Float("Base")
    venta_exp_porcent = fields.Selection([("8", "Alicuota reducida"), ("16", "Alicuota general"),
                                          ("24", "Alicuota más adicional")],
                                         string="Porcentaje de afecta", default="16")
    venta_exp_importe = fields.Float("Importe")

    venta_int_base = fields.Float("Base")
    venta_int_porcent = fields.Selection([("8", "Alicuota reducida"), ("16", "Alicuota general"),
                                          ("24", "Alicuota más adicional")],
                                         string="Porcentaje de afecta", default="16")
    venta_int_importe = fields.Float("Importe")

    venta_int_base_r = fields.Float("Base")
    venta_int_porcent_r = fields.Selection([("8", "Alicuota reducida")], string="Porcentaje de afecta", default="8")
    venta_int_importe_r = fields.Float("Importe")

    iva_retenido = fields.Float("I.V.A retenido")
    comprobante = fields.Char("Número de comprobante")
    periodos = fields.Float("NC o ND de periodos anteriores a ajustar")

    account_book_id = fields.Many2one('account.book.sale', string='Libro')
