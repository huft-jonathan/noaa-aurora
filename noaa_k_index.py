#!/usr/bin/python

"""
Downloads and parses K-Index forecasts and observations from
NOAA's Space Weather Prediction Center.

More information at:
<https://www.swpc.noaa.gov/products/planetary-k-index>
<https://en.wikipedia.org/wiki/K-index>
"""

__author__ = "D. Jonathan Huft"


import sys
import datetime
import logging

from noaa_data_source import NOAA_Data_Source
import util


class NOAA_Space_Weather_Data_Source(NOAA_Data_Source):
    """
    Parent for K-index observation and forecast classes.
    """

    BASE_URL = "https://services.swpc.noaa.gov/products/"
    NOAA_DT_FMT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, url, fpath):
        super().__init__(url=url, fpath=fpath)
        self._times = []

    @property
    def duration(self):
        """Duration of one forecast or observation period."""
        return self._times[1] - self._times[0]

    def _index(self, utc_datetime):
        """
        Return list index (or indices) corresponding to the given time
        (or endpoints of a range of time).
        """
        def _i(utc_datetime):
            for i, t in enumerate(self._times):
                if t <= utc_datetime < t + self.duration:
                    return i
            raise Exception("Time %s is out of range" % utc_datetime)

        if isinstance(utc_datetime, list):
            assert len(utc_datetime) == 2
            if utc_datetime[1] == "latest":
                return [_i(utc_datetime[0]), -2]
            return [_i(utc_datetime[0]), _i(utc_datetime[1])]
        return 2 * [_i(utc_datetime)]

    @staticmethod
    def single_or_list(a):
        """Be able to specify either single value or a list of values."""
        if len(a) == 1:
            return a[0]
        return a

    def _get_data(self, which, utc_datetime):
        self.lazy_get()
        a, b = self._index(utc_datetime)
        return self.single_or_list(getattr(self, which)[a:b + 1])


class NOAA_K_Index_Forecast(NOAA_Space_Weather_Data_Source):
    """
    Download and parse the planetary K-index forecast.

    Corresponding user-friendly webpage at:
    <https://www.swpc.noaa.gov/products/3-day-forecast>
    """

    def __init__(self, fpath="/tmp/noaa_k_index_fx.json"):
        super().__init__(
            url=self.BASE_URL + "noaa-planetary-k-index-forecast.json",
            fpath=fpath)

        self._times = []
        self._kps = []
        self._observeds = []
        self._noaa_scales = []

    def parse_data(self):
        assert self._data[0] == ['time_tag', 'kp', 'observed', 'noaa_scale']
        for x in self._data[1::]:
            self._times.append(
                datetime.datetime.strptime(x[0], self.NOAA_DT_FMT).replace(
                    tzinfo=datetime.timezone.utc))
            self._kps.append(int(x[1]))
            self._observeds.append(x[2])
            self._noaa_scales.append(x[3])

    # Data Methods _____________________________________________________________
    def forecast_time(self, utc_datetime):
        """Forecast period start time. (tz-aware datetime)"""
        return self._get_data("_times", utc_datetime)

    def kp(self, utc_datetime):
        """Planetary K-Index (integer)"""
        return self._get_data("_kps", utc_datetime)

    def observed(self, utc_datetime):
        """Type of observation: "observed", "estimated", or "predicted" """
        return self._get_data("_observeds", utc_datetime)

    def noaa_scale(self, utc_datetime):
        """R/S/G Scale, if any, otherwise None.
        <https://www.swpc.noaa.gov/noaa-scales-explanation>
        """
        return self._get_data("_noaa_scales", utc_datetime)

    # Misc Methods _____________________________________________________________
    def demo(self):
        """
        Print the forecasted K-indices for the next 24 hours.
        """

        now = util.now()
        later = now + datetime.timedelta(days=1, hours=0)

        print("PLANETARY K-INDEX FORECAST:")
        fmt = "%28s  %8s  %12s"
        print(fmt % ("Time", "K-index", "Type"))
        for a, b, c in zip(self.forecast_time([now, later]),
                           self.kp([now, later]),
                           self.observed([now, later])):
            print(fmt % (a, b, c.title()))


class NOAA_K_Index_1_Minute(NOAA_Space_Weather_Data_Source):
    """
    Download and parse one-minute K-index observations.

    Corresponding user-friendly webpage at:
    <https://www.swpc.noaa.gov/products/planetary-k-index>
    """

    def __init__(self, fpath="/tmp/noaa_k_index_1_min.json"):
        super().__init__(
            url=self.BASE_URL + "noaa-estimated-planetary-k-index-1-minute.json",
            fpath=fpath)

        self._times = []
        self._estimated_kps = []
        self._kps = []

    def parse_data(self):
        assert self._data[0] == ['time_tag', 'estimated_kp', 'kp']
        for x in self._data[1::]:
            self._times.append(
                datetime.datetime.strptime(x[0], self.NOAA_DT_FMT).replace(
                    tzinfo=datetime.timezone.utc))
            self._estimated_kps.append(float(x[1]))
            self._kps.append(x[2])

    # Data Methods _____________________________________________________________
    def forecast_time(self, utc_datetime):
        """Observation period start time. (tz-aware datetime)"""
        return self._get_data("_times", utc_datetime)

    def estimated_kp(self, utc_datetime):
        """Estimated planetary K-index (float)"""
        return self._get_data("_estimated_kps", utc_datetime)

    def kp(self, utc_datetime):
        """String such as "2P", "1Z", etc."""
        return self._get_data("_kps", utc_datetime)

    # Misc Methods _____________________________________________________________

    def demo(self):
        now = util.now()
        previouly1 = now - datetime.timedelta(hours=3)
        previouly2 = now - datetime.timedelta(hours=1)

        print("PLANETARY K-INDEX OBSERVATIONS:")
        fmt = "%28s  %8s"
        print(fmt % ("Time", "K-index"))

        for a, b in zip(self.forecast_time([previouly1, previouly2]),
                        self.estimated_kp([previouly1, previouly2])):
            print(fmt % (a, b))


if __name__ == "__main__":

    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    fx = NOAA_K_Index_Forecast()
    fx.demo()

    print(32 * "-")

    ob = NOAA_K_Index_1_Minute()
    ob.demo()
