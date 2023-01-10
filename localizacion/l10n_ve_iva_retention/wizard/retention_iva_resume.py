from odoo import fields, models
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class RetentionIvaResume(models.TransientModel):
    _name = 'retention.iva.resume.wizard'
    _description = 'Iva Resume'

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id)
    from_date = fields.Date(string='Date From', default=lambda *a: datetime.now().strftime('%Y-%m-%d'))
    to_date = fields.Date('Date To', default=lambda *a: (datetime.now() + relativedelta(years=1)).strftime('%Y-%m-%d'))

    def get_resume_iva(self):
        start_time = datetime.now()
        desde = fields.Date.from_string(self.from_date)
        hasta = fields.Date.from_string(self.to_date)
        query = """
            SELECT * FROM alicuota AS ali
            INNER JOIN account_tax_alicuota_rel AS tax_rel
            ON ali.id = tax_rel.alicuota_id
            INNER JOIN account_tax AS tax
            ON tax.id = account_tax_id
            WHERE date_invoice BETWEEN '%s' and '%s'
            AND state IN ('posted', 'cancel')
            AND move_type IN ('in_invoice','in_refund')
            AND retention_iva_state IN ('done')
        """ % (desde, hasta)
        self._cr.execute(query)
        obj_query = self._cr.dictfetchall()
        print(obj_query)
        for q in obj_query:
            q['total_amount_iva'] = self.amount_rate(q['total_amount_iva'], q['move_id'], q['currency_id'])
            q['total_exempt'] = self.amount_rate(q['total_exempt'], q['move_id'], q['currency_id'])
            q['base_reduced'] = self.amount_rate(q['base_reduced'], q['move_id'], q['currency_id'])
            q['ali_reduced'] = self.amount_rate(q['ali_reduced'], q['move_id'], q['currency_id'])
            q['base_additional'] = self.amount_rate(q['base_additional'], q['move_id'], q['currency_id'])
            q['ali_general'] = self.amount_rate(q['ali_general'], q['move_id'], q['currency_id'])
            q['ali_additional'] = self.amount_rate(q['ali_additional'], q['move_id'], q['currency_id'])
            q['total_ret_iva'] = self.amount_rate(q['total_ret_iva'], q['move_id'], q['currency_id'])
        end_time = datetime.now()
        _logger.info(">> ({}) {}: {}  | {}: {}".format(
            'get_resume_iva',
            'Hora de Inicio', start_time,
            'Tiempo de ejecucion', end_time - start_time))
        return obj_query

    def amount_rate(self, amount, move_id, currency_id):
        aux = 0
        result = 0
        if currency_id != self.company_id.currency_id.id:
            obj_move = self.env['account.move'].search([('id', '=', move_id)], order="id asc")
            for move in obj_move:
                aux += abs(move.amount_untaxed_signed / move.amount_untaxed)
            rate = round(aux, 2)
            result += amount * rate
        else:
            result = amount
        return result

    def print_report(self):
        return self.env.ref('l10n_ve_iva_retention.action_iva_retention_resume_report').report_action(self)
