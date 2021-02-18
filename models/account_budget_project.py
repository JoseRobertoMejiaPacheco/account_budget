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
    account_ids = fields.Many2many('account.account', 'account_budget_rel', 'budget_id', 'account_id', 'Accounts',
        domain=[('deprecated', '=', False)])
    crossovered_budget_line = fields.One2many('crossovered.budget.project.lines', 'general_budget_id', 'Budget Lines')
    company_id = fields.Many2one('res.company', 'Company', required=True,
        default=lambda self: self.env['res.company']._company_default_get('account.budget.post.project'))

    def _check_account_ids(self, vals):
        # Raise an error to prevent the account.budget.post to have not specified account_ids.
        # This check is done on create because require=True doesn't work on Many2many fields.
        if 'account_ids' in vals:
            account_ids = self.resolve_2many_commands('account_ids', vals['account_ids'])
        else:
            account_ids = self.account_ids
        if not account_ids:
            raise ValidationError(_('The budget must have at least one account.'))

    @api.model
    def create(self, vals):
        self._check_account_ids(vals)
        return super(AccountBudgetPost, self).create(vals)

    @api.multi
    def write(self, vals):
        self._check_account_ids(vals)
        return super(AccountBudgetPost, self).write(vals)


class CrossoveredBudgetProject(models.Model):
    _name = "crossovered.budget.project"
    _description = "Project Budget"
    _inherit = ['mail.thread']

    name = fields.Char('Budget Name', required=True, states={'done': [('readonly', True)]})
    creating_user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user)
    date_from = fields.Date('Start Date', required=True, states={'done': [('readonly', True)]})
    date_to = fields.Date('End Date', required=True, states={'done': [('readonly', True)]})    
    active= fields.Boolean(default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('confirm', 'Confirmed'),
        ('validate', 'Validated'),
        ('done', 'Done')
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

    crossovered_budget_id = fields.Many2one('crossovered.budget.project', 'Budget', ondelete='cascade', index=True, required=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    responsible_employee = fields.Many2one('res.users', 'Responsable del Presupuesto')
    general_budget_id = fields.Many2one('account.budget.post.project', 'Budgetary Position', required=True)
    date_from = fields.Date('Start Date', required=True)
    date_to = fields.Date('End Date', required=True)
    paid_date = fields.Date('Paid Date')
    planned_amount = fields.Float('Planned Amount', required=True, digits=0)
    practical_amount = fields.Float(compute='_compute_practical_amount', string='Practical Amount', digits=0)    
    percentage = fields.Float(compute='_compute_percentage', string='Achievement',store=True)
    company_id = fields.Many2one(related='crossovered_budget_id.company_id', comodel_name='res.company',
        string='Company', store=True, readonly=True)
    forecast=fields.Float()


    @api.multi
    def _compute_practical_amount(self):
        for line in self:
            result = 0.0
            acc_ids = line.general_budget_id.account_ids.ids
            date_to = self.env.context.get('wizard_date_to') or line.date_to
            date_from = self.env.context.get('wizard_date_from') or line.date_from
            acc_ids_str=""
            if line.analytic_account_id.id:                
                for item in acc_ids:
                    acc_ids_str=acc_ids_str+str(item)+','
                acc_ids_str=acc_ids_str.rstrip(acc_ids_str[-1])
            try:
                
                general_budget=self.env['account.move.line'].search([('date', '>=',date_from),('date', '<=',date_to),('account_id','in',acc_ids)])
                for item in general_budget:
                    result=result+item.credit-item.debit               
            except: result=0
                
            line.practical_amount = result
    # @api.multi
    # def _compute_practical_amount(self):
    #     print(self)
    #     for line in self:
    #         result = 0.0
    #         acc_ids = line.general_budget_id.account_ids.ids
    #         date_to = self.env.context.get('wizard_date_to') or line.date_to
    #         date_from = self.env.context.get('wizard_date_from') or line.date_from
    #         if line.analytic_account_id.id:
    #             self.env.cr.execute("""
    #                 SELECT SUM(amount)
    #                 FROM account_analytic_line
    #                 WHERE account_id=%s
    #                     AND (date between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd'))
    #                     AND general_account_id=ANY(%s)""",
    #             (line.analytic_account_id.id, date_from, date_to, acc_ids,))
    #             result = self.env.cr.fetchone()[0] or 0.0
    #         line.practical_amount = result


    @api.multi
    def open_record(self):        
        account_move_lines_filtered=self.env['account.move.line'].search([('date', '>=',self.date_from),('date', '<=',self.date_to),('account_id','in',self.general_budget_id.account_ids.ids)]).mapped('id')        
        return {
            'name':'Movimientos de: '+self.general_budget_id.display_name,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move.line',
            'type': 'ir.actions.act_window',
            'domain':[('id','in',account_move_lines_filtered)],            
            'target':'current'
        }

    @api.multi
    def _compute_percentage(self):
        for line in self:
            if line.practical_amount != 0.00:
                print("Real"+str(line.practical_amount))
                print("Planeado"+str(line.planned_amount))
                try:
                    line.percentage = float((line.practical_amount*100)/line.planned_amount)
                except:
                    line.percentage=0.0
            else:
                line.percentage = 0.00
