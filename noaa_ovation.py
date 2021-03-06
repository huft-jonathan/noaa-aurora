#!/usr/bin/python

"""
Downloads and parses forecasts based on the OVATION (Oval Variation,
Assessment, Tracking, Intensity, and Online Nowcasting) model from
NOAA's Space Weather Prediction Center.

More information at:
<https://www.swpc.noaa.gov/products/aurora-30-minute-forecast>
"""

__author__ = "D. Jonathan Huft"


import sys
import datetime
import logging

import noaa_k_index


class NOAA_Ovation(noaa_k_index.NOAA_Space_Weather_Data_Source):

    # Not the same as the other datetime formats in this package
    NOAA_DT_FMT = "%Y-%m-%dT%H:%M:%SZ"

    BASE_URL = "https://services.swpc.noaa.gov/json/"

    def __init__(self, fpath="ovation_aurora_latest.json"):
        super().__init__(
            url=self.BASE_URL + "ovation_aurora_latest.json",
            fpath=fpath)

        self._obs_time = None
        self._fx_time = None
        self._coords = []

    def parse_data(self):
        """
        Data is of the following format:

        {'Observation Time': '2021-01-18T03:36:00Z',
         'Forecast Time': '2021-01-18T05:08:00Z',
         'Data Format': '[Longitude, Latitude, Aurora]',
         'coordinates': [[0, -90, 2], [0, -89, 0], [0, -88, 2],
                         [0, -87, 3], [0, -86, 4], [0, -85, 5], ...]}
        """

        self._obs_time = datetime.datetime.strptime(
            self._data['Observation Time'],
            self.NOAA_DT_FMT).replace(tzinfo=datetime.timezone.utc)

        self._fx_time = datetime.datetime.strptime(
            self._data['Forecast Time'],
            self.NOAA_DT_FMT).replace(tzinfo=datetime.timezone.utc)

        for x in self._data['coordinates']:
            if x[0] >= 180:
                x[0] -= 360
            self._coords.append(x)

        self._data = 0

    # Data Methods _____________________________________________________________
    def forecast_time(self, utc_datetime):
        """Forecast period start time. (tz-aware datetime)"""
        return self._get_data("_times", utc_datetime)

    @property
    def obs_time(self):
        self.lazy_get()
        return self._obs_time

    @property
    def fx_time(self):
        self.lazy_get()
        return self._fx_time

    @property
    def coords(self):
        self.lazy_get()
        return self._coords

    def get_four_closest(self, lat, lon):
        lat1 = int(round(lat))
        lat2 = int(round(lat+1))

        lon1 = int(round(lon))
        lon2 = int(round(lon+1))

        ret = []
        for coord in self.coords:
            if (int(coord[1]) in [lat1, lat2] and int(coord[0]) in
                    [lon1, lon2]):
                ret.append(coord[2])
        assert len(ret) == 4
        return ret

    def estimated(self, lat, lon):
        return sum(self.get_four_closest(lat, lon)) / 4.0

    def plot(self, lat, lon):

        import matplotlib.pyplot as plt
        import random

        for coord in self.coords:
            if random.random() < 0.1:   # Don't bother plotting everything
                if coord[2] > 1:
                    plt.scatter(coord[0], coord[1], c="Green",
                                alpha=coord[2] / 100)

        plt.scatter(lon, lat, c="Red", alpha=0.9)
        plt.show()

    # Misc Methods _____________________________________________________________
    def demo(self):
        lat = 44.5
        lon = -103.9

        print(self.get_four_closest(lat, lon))
        print(self.estimated(lat, lon))
        self.plot(lat, lon)


if __name__ == "__main__":

    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    ov = NOAA_Ovation()
    ov.demo()
