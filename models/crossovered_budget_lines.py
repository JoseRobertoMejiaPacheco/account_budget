# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import ustr
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class CrossoveredBudgetLines(models.Model):
    _name = "crossovered.budget.lines"
    _description = "Budget Line"

    crossovered_budget_id = fields.Many2one('crossovered.budget', 'Budget', ondelete='cascade', index=True, required=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    responsible_employee = fields.Many2one('res.users', 'Responsable del Presupuesto')
    general_budget_id = fields.Many2one('account.budget.post', 'Budgetary Position', required=True)
    date_from = fields.Date('Start Date', required=True)
    date_to = fields.Date('End Date', required=True)
    paid_date = fields.Date('Paid Date')
    planned_amount = fields.Float('Planned Amount', required=True, digits=0)
    practical_amount = fields.Float(compute='_compute_practical_amount', string='Practical Amount', digits=0)    
    percentage = fields.Float(compute='_compute_percentage2', string='Practical Amount', digits=0)   
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
    def _compute_percentage2(self):
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
