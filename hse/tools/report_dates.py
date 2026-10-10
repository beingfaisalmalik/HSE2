"""Inclusive local calendar dates, translated to an exclusive UTC end bound."""
from datetime import datetime, time, timedelta

import pytz

from odoo import fields, _
from odoo.exceptions import UserError


def date_range_domain(env, field_name, start_date, end_date):
    start_date, end_date = fields.Date.to_date(start_date), fields.Date.to_date(end_date)
    if not start_date or not end_date:
        raise UserError(_('Choose both the From Date and To Date.'))
    if start_date > end_date:
        raise UserError(_('From Date cannot be after To Date.'))
    zone = pytz.timezone(env.context.get('tz') or env.user.tz or 'UTC')
    start = zone.localize(datetime.combine(start_date, time.min))
    end = zone.localize(datetime.combine(end_date + timedelta(days=1), time.min))
    def to_utc(value):
        return fields.Datetime.to_string(value.astimezone(pytz.UTC).replace(tzinfo=None))
    return [(field_name, '>=', to_utc(start)), (field_name, '<', to_utc(end))]
