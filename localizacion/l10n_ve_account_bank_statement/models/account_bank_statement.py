# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountBankStatement(models.Model):
	_inherit = "account.bank.statement"

	def action_organize_ref(self):
		for line in self.line_ids:
			if not line.validador:
				var_move_line = self.env['account.move.line'].search([('ref', '=', line.ref), ('balance', '=', line.amoun)])
				line.write({
					'name': line.name + "Nro Ref:" + line.ref,
					'partner_id': var_move_line.payment_id.partner_id.id,
					'validador': True
				})


class AccountBankStatementLine(models.Model):
	_inherit = "account.bank.statement.line"

	validador = fields.Boolean()
