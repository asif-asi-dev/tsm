# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import date
from odoo.exceptions import UserError, ValidationError



class AccountCashBookReport(models.TransientModel):
    _name = "account.cashbook.report"
    _description = "Cash Book Report"

    def _get_default_account_ids(self):
        journals = self.env['account.journal'].search([('type', '=', 'cash')])
        accounts = []
        for journal in journals:
            if journal.default_account_id.id:
                accounts.append(journal.default_account_id.id)
            if journal.company_id.account_journal_payment_credit_account_id.id:
                accounts.append(journal.company_id.account_journal_payment_credit_account_id.id)
            if journal.company_id.account_journal_payment_debit_account_id.id:
                accounts.append(journal.company_id.account_journal_payment_debit_account_id.id)
            for acc_out in journal.outbound_payment_method_line_ids:
                if acc_out.payment_account_id:
                    accounts.append(acc_out.payment_account_id.id)
            for acc_in in journal.inbound_payment_method_line_ids:
                if acc_in.payment_account_id:
                    accounts.append(acc_in.payment_account_id.id)
        return accounts

    operating_unit_id = fields.Many2one(  # Changed from operating_unit_ids to operating_unit_id
        comodel_name="operating.unit",
        string="Operating Unit"
    )
    date_range_id = fields.Many2one(comodel_name="date.range", string="Date range")
    date_from = fields.Date(string='Start Date', default=date.today(), required=True)
    date_to = fields.Date(string='End Date', default=date.today(), required=True)
    target_move = fields.Selection([('posted', 'Posted Entries'),
                                    ('all', 'All Entries')], string='Target Moves', required=True,
                                   default='posted')
    journal_ids = fields.Many2many('account.journal', string='Journals', required=True,
                                   default=lambda self: self.env['account.journal'].search([('type','=', 'cash')]))
    account_ids = fields.Many2many('account.account', 'account_account_cashbook_report', 'report_line_id',
                                   'account_id', 'Accounts', default=_get_default_account_ids)

    display_account = fields.Selection(
        [('all', 'All'), ('movement', 'With movements'),
         ('not_zero', 'With balance is not equal to 0')],
        string='Display Accounts', required=True, default='movement')
    sortby = fields.Selection(
        [('sort_date', 'Date'), ('sort_journal_partner', 'Journal & Partner')],
        string='Sort by',
        required=True, default='sort_date')
    initial_balance = fields.Boolean(string='Include Initial Balances',
                                     help='If you selected date, this field allow you to add a row to'
                                          ' display the amount of debit/credit/balance that precedes '
                                          'the filter you\'ve set.')
    report_type = fields.Selection([
        ("detailed", "Detailed"),
        ("summary", "Summary"),
    ], string="Report Type", default='detailed')

    @api.onchange("date_from", "date_to", "date_range_id")
    def _check_dates_within_date_range(self):
        for rec in self:
            if rec.date_range_id:
                date_range = rec.date_range_id
                if rec.date_from and (
                        rec.date_from < date_range.date_start
                        or rec.date_from > date_range.date_end
                ):
                    raise ValidationError(
                        _("The 'Start Date' must be within the date range: %s to %s.")
                        % (date_range.date_start, date_range.date_end)
                    )
                if rec.date_to and (
                        rec.date_to < date_range.date_start
                        or rec.date_to > date_range.date_end
                ):
                    raise ValidationError(
                        _("The 'End Date' must be within the date range: %s to %s.")
                        % (date_range.date_start, date_range.date_end)
                    )

    @api.onchange("date_range_id")
    def onchange_date_range_id(self):
        """Handle date range change."""
        self.date_from = self.date_range_id.date_start
        self.date_to = self.date_range_id.date_end

    @api.onchange('account_ids')
    def onchange_account_ids(self):
        if self.account_ids:
            journals = self.env['account.journal'].search(
                [('type', '=', 'cash')])
            accounts = []
            for journal in journals:
                accounts.append(journal.company_id.account_journal_payment_credit_account_id.id)
            domain = {'account_ids': [('id', 'in', accounts)]}
            return {'domain': domain}

    def _build_comparison_context(self, data):
        result = {}
        result['journal_ids'] = data['form'].get('journal_ids', False)
        result['state'] = data['form'].get('target_move', 'posted')
        result['date_from'] = data['form'].get('date_from', False)
        result['date_to'] = data['form'].get('date_to', False)
        result['strict_range'] = True if result['date_from'] else False
        result['operating_unit_id'] = data['form'].get('operating_unit_id', False) and \
                                      data['form']['operating_unit_id'][0] if isinstance(
            data['form'].get('operating_unit_id'), (list, tuple)) else data['form'].get('operating_unit_id')

        return result

    def check_report(self):
        self.ensure_one()
        data = {}
        data['form'] = self.read([
            'target_move', 'date_from', 'date_to', 'journal_ids', 'account_ids',
            'sortby', 'initial_balance', 'display_account', 'operating_unit_id'
        ])[0]
        if data['form'].get('operating_unit_id'):
            if isinstance(data['form']['operating_unit_id'], (list, tuple)):
                data['form']['operating_unit_id'] = data['form']['operating_unit_id'][0]
        comparison_context = self._build_comparison_context(data)
        data['form']['comparison_context'] = comparison_context
        return self.env.ref('om_account_daily_reports.action_report_cash_book').report_action(self, data=data)

