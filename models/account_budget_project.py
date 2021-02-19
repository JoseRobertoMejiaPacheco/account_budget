# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import ustr
from odoo.exceptions import UserError, ValidationError
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


class CrossoveredBudgetProject(models.Model):
    _name = "crossovered.budget.project"
    _description = "Project Budget"
    _inherit = ['mail.thread']

    name = fields.Many2one('account.analytic.account',
                           'Nombre / Cuenta Analítica')
    #name = fields.Char('Budget Name', required=True, states={'done': [('readonly', True)]})
    creating_user_id = fields.Many2one(
        'res.users', 'Responsable', default=lambda self: self.env.user)
    active = fields.Boolean(default=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('cancel', 'Cancelado'),
        ('confirm', 'Confirmado'),
        ('validate', 'Validado'),
        ('done', 'Hecho')
    ], 'Status', default='draft', index=True, required=True, readonly=True, copy=False, track_visibility='always')
    crossovered_budget_line = fields.One2many('crossovered.budget.project.lines', 'crossovered_budget_id', 'Budget Lines',
                                              states={'done': [('readonly', True)]}, copy=True)
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get('account.budget.post.project'))

    @api.multi
    def action_budget_confirm(self):
        self.write({'state': 'confirm'})

    @api.multi
    def action_budget_draft(self):
        self.write({'state': 'draft'})

    @api.multi
    def action_budget_validate(self):
        self.write({'state': 'validate'})

    @api.multi
    def action_budget_cancel(self):
        self.write({'state': 'cancel'})

    @api.multi
    def action_budget_done(self):
        self.write({'state': 'done'})


class CrossoveredBudgetLinesProject(models.Model):
    _name = "crossovered.budget.project.lines"
    _description = "Budget Line"

    crossovered_budget_id = fields.Many2one(
        'crossovered.budget.project', 'Presupuesto', ondelete='cascade', index=True, required=True)
    # analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    responsible_employee = fields.Many2one(
        'res.users', 'Responsable de la Cuenta')
    general_budget_id = fields.Many2one(
        'account.budget.post.project', 'Posición Presupuestaria', required=True)
    paid_date = fields.Date('Fecha de Pago')
    planned_amount = fields.Float('Importe Planeado', required=True, digits=0)
    practical_amount = fields.Float(
        compute='_compute_practical_amount', string='Importe Real', digits=0)
    #practical_amount2 = fields.Float(
    #    compute='_compute_percentage2', string='Logro', store=True)
    company_id = fields.Many2one(related='crossovered_budget_id.company_id', comodel_name='res.company',
                                 string='Company', store=True, readonly=True)
    forecast = fields.Float()

    # @api.multi
    # def _compute_percentage2(self):
    #     print("X")
    @api.multi
    def _compute_practical_amount(self):
        # crossovered.budget.project.lines(1,)
        # print(self.crossovered_budget_id.name.id)
        print(self)
        for line in self:
            result = 0.0
            acc_ids = line.general_budget_id.account_ids.ids
            acc_ids_str = ""
            if line.crossovered_budget_id.name.id:
                for item in acc_ids:
                    acc_ids_str = acc_ids_str+str(item)+','
                acc_ids_str = acc_ids_str.rstrip(acc_ids_str[-1])
            try:
                general_budget = self.env['account.move.line'].search(
                    [('analytic_account_id', '=', self.crossovered_budget_id.name.id), ('account_id', 'in', acc_ids)])
                for item in general_budget:
                    result = result+item.credit-item.debit
            except:
                result = 0

            line.practical_amount = result


    @api.multi
    def open_record(self):
        print(self)
        account_move_lines_filtered = self.env['account.move.line'].search(
            [('analytic_account_id', '=', self.crossovered_budget_id.name.id), ('account_id', 'in', self.general_budget_id.account_ids.ids)]).mapped('id')
        return {
            'name': 'Movimientos de: '+self.general_budget_id.display_name,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move.line',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', account_move_lines_filtered)],
            'target': 'current'
        }


