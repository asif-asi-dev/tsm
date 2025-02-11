# -*- coding: utf-8 -*-
from email.policy import default

from odoo import fields, models, _, api
from datetime import date
from odoo.exceptions import UserError, ValidationError
import urllib



class AccountDayBookReport(models.TransientModel):
    _name = "account.daybook.report"
    _description = "Day Book Report"

    operating_unit_id = fields.Many2one(  # Changed from operating_unit_ids to operating_unit_id
        comodel_name="operating.unit",
        string="Operating Unit"
    )
    report_type = fields.Selection([
            ("detailed", "Detailed"),
            ("summary", "Summary"),
        ], string="Report Type", default='detailed')
    date_range_id = fields.Many2one(comodel_name="date.range", string="Date range")
    date_from = fields.Date(string='Start Date', required=True)
    date_to = fields.Date(string='End Date', required=True)
    target_move = fields.Selection([('posted', 'Posted Entries'),
                                    ('all', 'All Entries')], string='Target Moves', required=True,
                                   default='posted')
    journal_ids = fields.Many2many('account.journal', string='Journals', required=True,
                                   default=lambda self: self.env['account.journal'].search([]))
    account_ids = fields.Many2many('account.account', 'account_account_daybook_report', 'report_line_id',
                                   'account_id', 'Accounts')

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

    def _build_comparison_context(self, data):
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        result['date_from'] = data['form']['date_from']
        result['date_to'] = data['form']['date_to']
        # Pass only the ID of operating unit
        result['operating_unit_id'] = data['form'].get('operating_unit_id', False) and data['form']['operating_unit_id'][0] if isinstance(data['form'].get('operating_unit_id'), (list, tuple)) else data['form'].get('operating_unit_id')
        return result

    def check_report(self):
        data = {}
        # Read only the ID for operating_unit_id
        data['form'] = self.read(['target_move', 'date_from', 'date_to', 'journal_ids', 'account_ids', 'operating_unit_id'])[0]
        # Ensure we get only the ID from the Many2one field
        if data['form'].get('operating_unit_id'):
            if isinstance(data['form']['operating_unit_id'], (list, tuple)):
                data['form']['operating_unit_id'] = data['form']['operating_unit_id'][0]
        comparison_context = self._build_comparison_context(data)
        data['form']['comparison_context'] = comparison_context
        return self.env.ref('om_account_daily_reports.action_report_day_book').report_action(self, data=data)




