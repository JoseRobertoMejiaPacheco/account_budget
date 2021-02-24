# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import ustr
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp
from datetime import datetime

class CrossoveredBudgetProject(models.Model):
    _name = "crossovered.budget.project"
    _description = "Project Budget"
    _inherit = ['mail.thread']

    name = fields.Many2one('account.analytic.account',
                           'Nombre / Cuenta Analítica')
    other_currency = fields.Boolean(
        'Cotización en USD', required=True, default=False)
    tasa_usd = fields.Many2one('res.currency.rate',
                               'Tasa de cambio USD')            
    creating_user_id = fields.Many2one(
        'res.users', 'Responsable', default=lambda self: self.env.user)
    active = fields.Boolean(default=True)
    prueba = fields.Boolean(default=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('cancel', 'Cancelado'),
        ('confirm', 'Confirmado'),
        ('validate', 'Validado'),
        ('done', 'Hecho')
    ], 'Status', default='draft', index=True, required=True, readonly=True, copy=False, track_visibility='always')
    crossovered_budget_line = fields.One2many('crossovered.budget.project.lines', 'crossovered_budget_id', 'Budget Lines',
                                              states={'done': [('readonly', True)]}, copy=True)
    crossovered_budget_line_usd = fields.One2many('crossovered.budget.project.lines.usd', 'crossovered_budget_id', 'Budget Lines',
                                                  states={'done': [('readonly', True)]}, copy=True)
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get('account.budget.post.project'))
    computado = fields.Float(compute='compute_fun')

    def compute_fun(self):
        try:
            self.computado = 1/self.tasa_usd.rate
        except: self.computado=0.0

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
    
    @api.multi
    def hola(self):
        self.write({'other_currency': not self.other_currency})