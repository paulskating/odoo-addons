# _*_ coding: utf-8 _*_
from openerp.fields import Datetime
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.misc import DEFAULT_SERVER_TIME_FORMAT
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT


class TimeZoneHelper(object):
    def __init__(self, tz):
        self._context = {"tz": tz}


TimeZoneHelper_TW = TimeZoneHelper(u'Etc/GMT+8')
TimeZoneHelper_TW2 = TimeZoneHelper(u'Etc/GMT-8')


def UTC_String_From_TW_TZ(timestr):
    if not timestr:
        return None

    dt_time =UTC_Datetime_From_TW_TZ(timestr)
    return Datetime.to_string(dt_time)


def UTC_Datetime_From_TW_TZ(timestr):
    if not timestr:
        return None

    return Datetime.context_timestamp(TimeZoneHelper_TW, Datetime.from_string(timestr))



def UTC_String_To_TW_TZ(timestr):
    if not timestr:
        return None

    dt_time = UTC_Datetime_To_TW_TZ(timestr)
    return Datetime.to_string(dt_time)


def UTC_Datetime_To_TW_TZ(timestr):
    if not timestr:
        return None

    return Datetime.context_timestamp(TimeZoneHelper_TW2, Datetime.from_string(timestr))
