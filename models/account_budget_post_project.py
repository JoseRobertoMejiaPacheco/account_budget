# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import ustr
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp
from datetime import datetime


# ---------------------------------------------------------
# Budgets
# ---------------------------------------------------------
class AccountBudgetPostProject(models.Model):
    _name = "account.budget.post.project"
    _order = "name"
    _description = "Budgetary Position Project"

    name = fields.Char('Name', required=True)
    account_ids = fields.Many2many('account.account', 'account_budget_project_rel', 'budget_id', 'account_id', 'Accounts',
                                   domain=[('deprecated', '=', False)])
    crossovered_budget_line = fields.One2many(
        'crossovered.budget.project.lines', 'general_budget_id', 'Budget Lines')
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get('account.budget.post.project'))
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get('account.budget.post.project'))

    def _check_account_ids(self, vals):
        # Raise an error to prevent the account.budget.post to have not specified account_ids.
        # This check is done on create because require=True doesn't work on Many2many fields.
        if 'account_ids' in vals:
            account_ids = self.resolve_2many_commands(
                'account_ids', vals['account_ids'])
        else:
            account_ids = self.account_ids
        if not account_ids:
            raise ValidationError(
                _('The budget must have at least one account.'))

    @api.model
    def create(self, vals):
        self._check_account_ids(vals)
        return super(AccountBudgetPostProject, self).create(vals)

    @api.multi
    def write(self, vals):
        self._check_account_ids(vals)
        return super(AccountBudgetPostProject, self).write(vals)



 