#!/usr/bin/python

"""
Uses K-index data from NOAA's Space Weather Prediction Center to determine if
the aurora are likely to be visible.

To determine the minimum K-index at which the aurora can be expected to be
visible in your area, refer to the following maps:

 - <https://commons.wikimedia.org/wiki/File:Aurora_Kp_Map_North_America.gif#/media/File:Aurora_Kp_Map_North_America.gif>
 - <https://commons.wikimedia.org/wiki/File:Aurora_Kp_Map_Eurasia.gif#/media/File:Aurora_Kp_Map_Eurasia.gif>

"""

__author__ = "D. Jonathan Huft"


import argparse
import datetime
import logging
import sys

import noaa_k_index
import util


class NOAA_Aurora():
    """
    Contains a few convenience methods to determine if aurora are likely.
    """

    def __init__(self, visible_k_index=None):
        """
        visible_k_index: the minimum K-index at which the aurora are expected
                         to be visible.
        """
        self.k_index_fx = noaa_k_index.NOAA_K_Index_Forecast()
        self.k_index_obs = noaa_k_index.NOAA_K_Index_1_Minute()

        if visible_k_index is None:
            self.visible_k_index = 5
        else:
            self.visible_k_index = visible_k_index

    @property
    def highest_kp_tonight(self):
        return max(self.k_index_fx.kp(util.night(day_offset=0)))

    @property
    def highest_kp_tomorrow(self):
        return max(self.k_index_fx.kp(util.night(day_offset=1)))

    @property
    def highest_recent_kp(self):
        start = util.now() - datetime.timedelta(minutes=60)
        return max(self.k_index_obs.estimated_kp([start, "latest"]))

    @property
    def visible_tonight(self):
        return (self.highest_kp_tonight > self.visible_k_index or
                self.highest_recent_kp > self.visible_k_index)

    @property
    def two_day_text_forecast(self):
        s = "Planetary K-Index forecast:\n"
        for n in (0, 1):
            for t, k in zip(self.k_index_fx.forecast_time(util.night(n)),
                            self.k_index_fx.kp(util.night(n))):
                s += "%s    %i\n" % (t.strftime(util.DT_FMT), k)
        return s


def get_arg_parser():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "-f",
        '--format',
        default="simple",
        choices=("visible_tonight", "simple", "text_forecast"),
        help="Chose a format for the output.")
    parser.add_argument(
        "-k",
        '--visible_k_index',
        default=None,
        type=float,
        help="The minimum K-index at which the aurora is expected to be "
             "visible locally (varies by lattitude).")
    parser.add_argument(
        "-l",
        '--logging_level',
        default=logging.WARNING,
        help="A standard logging level (CRITICAL ERROR WARNING INFO or DEBUG).")
    return parser


if __name__ == "__main__":

    args = get_arg_parser().parse_args()
    logging.basicConfig(stream=sys.stdout,
                        level=logging.getLevelName(args.logging_level))

    a = NOAA_Aurora(visible_k_index=args.visible_k_index)

    if args.format == "visible_tonight":
        print("Visible tonight." if a.visible_tonight else "Not visible tonight.")

    elif args.format == "simple":
        print("Maximum Planetary K-Index:")
        print("Tonight: %i" % a.highest_kp_tonight, end="  ")
        print("Tomorrow: %i" % a.highest_kp_tomorrow, end="  ")
        print("Recently: %.2f" % a.highest_recent_kp)

    elif args.format == "text_forecast":
        print(a.two_day_text_forecast)
