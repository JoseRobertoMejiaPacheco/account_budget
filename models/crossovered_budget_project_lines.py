# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import ustr
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp
from datetime import datetime

class CrossoveredBudgetLinesProject(models.Model):
    _name = "crossovered.budget.project.lines"
    _description = "Budget Line"

    crossovered_budget_id = fields.Many2one(
        'crossovered.budget.project', 'Presupuesto', ondelete='cascade', index=True, required=True)
    # analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    responsible_employee = fields.Many2one(
        'res.users', 'Responsable de la Cuenta')
    general_budget_id = fields.Many2one('account.budget.post.project', 'Posición Presupuestaria', required=True)
    paid_date = fields.Date('Fecha de Pago')
    planned_amount = fields.Float(string='Importe Planeado', required=True, digits=0)
    practical_amount = fields.Float(
        compute='_compute_practical_amount', string='Importe Real', digits=0)
    practical_amount2 = fields.Float(compute='_compute_percentage_')
    company_id = fields.Many2one(related='crossovered_budget_id.company_id', comodel_name='res.company',
                                 string='Company', store=True, readonly=True)
    practical_amount_mxn = fields.Float(
        compute='_compute_practical_amount_mxn', string='Importe Real USD', digits=0)
    
    @api.depends('practical_amount')
    def _compute_practical_amount_mxn(self):        
        self.practical_amount_mxn= 10/3

    
    def _compute_percentage_(self):
        # crossovered.budget.project.lines(1,)
        for line in self:
            if line.practical_amount != 0.00:
                print("Real"+str(line.practical_amount))
                print("Planeado"+str(line.planned_amount))
                try:
                    line.practical_amount2 = abs(float(
                        (abs(line.practical_amount)*100)/abs(line.planned_amount)))
                except:
                    line.practical_amount2 = 0.0
            else:
                line.practical_amount2 = 0.00

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
                    [('analytic_account_id', '=', line.crossovered_budget_id.name.id), ('account_id', 'in', acc_ids)])
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
