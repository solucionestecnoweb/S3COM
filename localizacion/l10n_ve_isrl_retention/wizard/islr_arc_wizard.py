from odoo import fields, models
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class IslrArcWizard(models.TransientModel):
    _name = 'islr.arc.wizard'
    _description = 'reporte arc islr'

    partner_id = fields.Many2one('res.partner', string='Proveedor')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id)
    from_date = fields.Date(string='Date From', default=lambda *a: datetime.now().strftime('%Y-%m-%d'))
    to_date = fields.Date('Date To', default=lambda *a: (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'))

    def get_islr_arc(self):
        start_time = datetime.now()
        desde = fields.Date.from_string(self.from_date)
        hasta = fields.Date.from_string(self.to_date)
        query = """
            SELECT 
                islr.id,
                islr.partner_id,
                islr.move_type,
                islr.name,
                islr.move_date,
                islr.invoice_number_next,
                islr.invoice_number_control,
                islr.invoice_number_unique,
                islr.amount_total,
                islr.amount_total_retention,
                line.base,
                line.qty,
                co.name AS concept
            from isrl_retention AS islr
            INNER JOIN isrl_retention_line AS line
            ON islr.id = line.retention_id
            INNER JOIN islr_concept AS co
            ON line.islr_concept_id = co.id
            WHERE islr.move_date BETWEEN '%s' AND '%s'
            AND islr.move_type in ('in_invoice', 'in_refund')
            AND islr.company_id = %s
            ORDER BY islr.move_date
        """ % (desde, hasta, self.company_id.id)
        self._cr.execute(query)
        obj_query = self._cr.dictfetchall()
        end_time = datetime.now()
        _logger.info(">> ({}) {}: {}  | {}: {}".format(
            'get_islr_arc',
            'Hora de Inicio', start_time,
            'Tiempo de ejecucion', end_time - start_time))
        return obj_query

    def print_report(self):
        return self.env.ref('l10n_ve_isrl_retention.action_islr_retention_arc_report').report_action(self)
