#!/usr/bin/python

import datetime
import logging

import tzlocal

T_FMT = "%H:%M %Z"
DT_FMT = "%Y-%m-%d %H:%M:%S %Z"

NIGHT_BEGIN_HOUR = 17
NIGHT_END_HOUR = 4


def now():
    return tzlocal.get_localzone().localize(datetime.datetime.now())


def night(day_offset=0):
    """
    Return tz-aware UTC times corresponding to the beginning and end of tonight.
    If it still isn't morning yet, these times may include the previous day.
    """

    h = now().replace(minute=0, second=0, microsecond=0)
    h += datetime.timedelta(days=day_offset)

    if h.hour < NIGHT_END_HOUR:
        # If not "morning" yet, look back.
        x = h - datetime.timedelta(days=1)
        y = h
    else:
        # If already "morning", look forward.
        x = h
        y = h + datetime.timedelta(days=1)

    begin = x.replace(hour=NIGHT_BEGIN_HOUR)
    end = y.replace(hour=NIGHT_END_HOUR)

    begin_utc = begin.astimezone(datetime.timezone.utc)
    end_utc = end.astimezone(datetime.timezone.utc)

    logging.debug("Night begins at %s." % begin_utc.strftime(DT_FMT))
    logging.debug("Night ends at %s." % end_utc.strftime(DT_FMT))

    return [begin_utc, end_utc]
