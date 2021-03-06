#!/usr/bin/python

__author__ = "D. Jonathan Huft"


from abc import ABC, abstractmethod
import time
import os
import json
import logging
import requests


DEFAULT_REFRESH_S = 60 * 30


class NOAA_Data_Source(ABC):
    """
    Intelligently download JSON files from NOAA and save them to disk.

    Limit the rate of download attempts, even if there are problems
    retrieving the data.

    Download new data at a specified rate.
    """

    def __init__(self, url, fpath, refresh_s=DEFAULT_REFRESH_S):

        self._data = None

        self._url = url
        self._fpath = os.path.expanduser(fpath)
        self._refresh_s = refresh_s

        if not os.path.isfile(self._fpath):
            logging.debug("File %s does not exist." % self._fpath)

            # First, try to create the file. This ensures that we will crash
            # before attempting a download if it's not possible to create the
            # file.
            self.save_data_to_file()

            # Set modification time to beginning of epoch, ensuring an
            # initial refresh of the file.
            os.utime(self._fpath, (0, 0))

    @property
    def needs_update(self):
        """File modification time determines when the next update is required."""
        if not os.path.isfile(self._fpath):
            return True

        age = time.time() - os.path.getmtime(self._fpath)
        if age > self._refresh_s:
            logging.debug("File is %i seconds old and needs to be updated." % age)
            return True
        return False

    def download(self):
        """Download a file, parse the JSON, and save."""

        self.touch_file()   # Prevents an immediate retry if anything fails

        headers = {'user-agent':
                   'noaa-aurora, '
                   'https://github.com/huft-jonathan/noaa-aurora'}

        logging.info("Making HTTP request to %s.." % self._url)
        try:
            response = requests.get(self._url, headers=headers)
        except requests.exceptions.ConnectionError as e:
            logging.error(e)
            raise
        if not response.ok:
            for k in ["url", "ok", "reason", "status_code", "text"]:
                logging.error("%s: %s" % (k, getattr(response, k)))
            raise Exception("Could not download data!")
        self._data = json.loads(response.text)
        self.save_data_to_file()

    def touch_file(self):
        now = time.time()
        os.utime(self._fpath, (now, now))

    def save_data_to_file(self):
        with open(self._fpath, 'w') as f:
            f.write(json.dumps(self._data))

    def load_data_from_file(self):
        with open(self._fpath, 'r') as f:
            x = f.read()
        self._data = json.loads(x)

    @abstractmethod
    def parse_data(self):
        """Must be implemented for each data source."""

    def lazy_get(self):
        if self.needs_update:
            self.download()
            self.parse_data()
        elif self._data is None:
            self.load_data_from_file()
            self.parse_data()
