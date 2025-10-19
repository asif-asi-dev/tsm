from odoo import models, api, _

TRACKED_FIELDS = {
    'name': 'Product Name',
    'list_price': 'Sales Price',
    'standard_price': 'Cost',
    'default_code': 'Internal Reference',
    'categ_id': 'Product Category',
    'uom_id': 'Unit of Measure',
    'uom_po_id': 'Purchase Unit of Measure',
    'product_variant_ids': 'Product Variants',
    'sale_ok': 'Can be Sold',
    'purchase_ok': 'Can be Purchased',
    'active': 'Active Status',
    'attribute_line_ids': 'Product Attributes',
}


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _get_tracking_mode(self):
        """Get tracking mode from system parameters."""
        return self.env['ir.config_parameter'].sudo().get_param(
            'ults_product_chatter.tracking_mode', 'specific'
        )

    def _get_fields_to_track(self):
        """Get fields to track based on configuration mode."""
        tracking_mode = self._get_tracking_mode()

        if tracking_mode == 'all':
            fields_to_track = {}
            exclude_fields = {
                'id', 'create_date', 'create_uid', 'write_date', 'write_uid',
                '__last_update', 'display_name', 'message_follower_ids',
                'message_ids', 'message_main_attachment_id', 'website_message_ids',
                'message_has_error', 'message_has_error_counter', 'message_has_sms_error',
                'message_attachment_count', 'message_is_follower', 'message_partner_ids',
                'message_needaction', 'message_needaction_counter', 'message_unread',
                'message_unread_counter', 'rating_ids', 'website_id',
            }

            for field_name, field in self._fields.items():
                if field_name in exclude_fields:
                    continue
                if hasattr(field, 'tracking') and field.tracking:
                    continue
                if (field.compute and not field.store) or field.related:
                    continue
                if field.automatic or field_name.startswith('_'):
                    continue

                fields_to_track[field_name] = field.string or field_name.replace(
                    '_', ' ').title()

            return fields_to_track
        else:
            return TRACKED_FIELDS

    def _format_one2many_detailed(self, field_name, old_value, new_value, old_data=None):
        """Format One2many changes with added/removed/modified details."""
        changes = []
        old_ids = set(old_value.ids) if old_value else set()
        new_ids = set(new_value.ids) if new_value else set()

        added_ids = new_ids - old_ids
        if added_ids:
            try:
                added_records = new_value.filtered(lambda r: r.id in added_ids)
                added_names = [
                    rec.display_name for rec in added_records if rec.display_name]
                if added_names:
                    changes.append(_('Added: %s') % ', '.join(added_names))
            except Exception:
                changes.append(_('Added: %d record(s)') % len(added_ids))

        removed_ids = old_ids - new_ids
        if removed_ids:
            if old_data:
                removed_names = [old_data.get(
                    rid) for rid in removed_ids if old_data.get(rid)]
                if removed_names:
                    changes.append(_('Removed: %s') % ', '.join(removed_names))
                else:
                    changes.append(_('Removed: %d record(s)') %
                                   len(removed_ids))
            else:
                try:
                    removed_records = old_value.filtered(
                        lambda r: r.id in removed_ids)
                    removed_names = [
                        rec.display_name for rec in removed_records if rec.display_name]
                    if removed_names:
                        changes.append(_('Removed: %s') %
                                       ', '.join(removed_names))
                    else:
                        changes.append(_('Removed: %d record(s)') %
                                       len(removed_ids))
                except Exception:
                    changes.append(_('Removed: %d record(s)') %
                                   len(removed_ids))

        return changes

    def _format_field_value(self, field_name, value, detailed=False, old_value=None, old_data=None):
        """Format field value based on type (Char, Float, Integer, Boolean, Many2one, One2many, Many2many, Selection, Date)."""
        field = self._fields.get(field_name)
        if not field:
            return str(value) if value else _('Empty')

        field_type = field.type

        if field_type == 'boolean':
            return _('Yes') if value else _('No')

        if not value:
            return _('Empty')

        if field_type == 'many2one':
            return value.display_name if hasattr(value, 'display_name') else str(value)

        elif field_type == 'one2many':
            if detailed and old_value is not None:
                detail_changes = self._format_one2many_detailed(
                    field_name, old_value, value, old_data=old_data)
                if detail_changes:
                    return '<br/>'.join(detail_changes)
            if hasattr(value, 'mapped'):
                names = value.mapped('display_name')
                if names:
                    return ', '.join(names)
            return _('Empty')

        elif field_type == 'many2many':
            if hasattr(value, 'mapped'):
                names = value.mapped('display_name')
                if names:
                    return ', '.join(names)
            return _('Empty')

        elif field_type in ('float', 'monetary'):
            return '{:,.2f}'.format(value)

        elif field_type == 'integer':
            return '{:,}'.format(value)

        elif field_type == 'selection':
            selection_dict = dict(field._description_selection(self.env))
            return selection_dict.get(value, str(value))

        elif field_type in ('date', 'datetime'):
            return str(value)

        return str(value)

    def _compare_values(self, field_name, old_value, new_value):
        """Compare values based on field type. Returns True if different."""
        field = self._fields.get(field_name)
        if not field:
            return old_value != new_value

        field_type = field.type

        if field_type == 'many2one':
            old_id = old_value.id if old_value else False
            new_id = new_value.id if new_value else False
            return old_id != new_id

        elif field_type in ('one2many', 'many2many'):
            old_ids = set(old_value.ids) if old_value else set()
            new_ids = set(new_value.ids) if new_value else set()
            return old_ids != new_ids

        return old_value != new_value

    def write(self, vals):
        """Track field changes and log to chatter. Supports all field types with configurable tracking modes."""
        fields_to_track = self._get_fields_to_track()
        old_values = {}
        old_one2many_data = {}

        for field_name in fields_to_track:
            if field_name in vals:
                old_values[field_name] = {}
                field = self._fields.get(field_name)
                is_one2many = field and field.type == 'one2many'

                for record in self:
                    old_value = record[field_name]
                    old_values[field_name][record.id] = old_value

                    if is_one2many and old_value:
                        if field_name not in old_one2many_data:
                            old_one2many_data[field_name] = {}
                        if record.id not in old_one2many_data[field_name]:
                            old_one2many_data[field_name][record.id] = {}

                        try:
                            for rec in old_value:
                                old_one2many_data[field_name][record.id][rec.id] = rec.display_name
                        except Exception:
                            pass

        result = super(ProductTemplate, self).write(vals)

        for record in self:
            changes = []

            for field_name, field_label in fields_to_track.items():
                if field_name in vals:
                    old_value = old_values[field_name].get(record.id)
                    new_value = record[field_name]

                    if self._compare_values(field_name, old_value, new_value):
                        field = self._fields.get(field_name)
                        is_one2many = field and field.type == 'one2many'

                        if is_one2many:
                            old_str = self._format_field_value(
                                field_name, old_value, detailed=False)
                            one2many_old_data = None
                            if field_name in old_one2many_data and record.id in old_one2many_data[field_name]:
                                one2many_old_data = old_one2many_data[field_name][record.id]
                            new_str = self._format_field_value(
                                field_name, new_value, detailed=True,
                                old_value=old_value, old_data=one2many_old_data)
                        else:
                            old_str = self._format_field_value(
                                field_name, old_value)
                            new_str = self._format_field_value(
                                field_name, new_value)

                        changes.append(
                            '<li>'
                            '<span style="font-weight: bold; color: #6c757d;">%s</span> '
                            '→ '
                            '<span style="font-weight: bold; color: #17a2b8;">%s</span> '
                            '<span style="font-style: italic; color: #6c757d;">(%s)</span>'
                            '</li>' % (old_str, new_str, field_label)
                        )

            if changes:
                try:
                    message = '<ul class="mb-0">' + "".join(changes) + "</ul>"
                    # Use sudo() to post message as system to avoid permission issues
                    record.sudo().message_post(body=message)
                except Exception as e:
                    # Log error but don't block the write operation
                    import logging
                    _logger = logging.getLogger(__name__)
                    _logger.warning(
                        'Could not post tracking message for product %s (ID: %s): %s',
                        record.name if hasattr(record, 'name') else 'Unknown',
                        record.id if hasattr(record, 'id') else 'Unknown',
                        str(e)
                    )

        return result
