# -*- coding:utf8 -*-

from __future__ import unicode_literals

from pyquery import PyQuery
import requests
import json
import datetime

try:
    from urllib import urlencode
except ImportError:
    # python 3
    from urllib.parse import urlencode


class ESTScraper(object):
    """
    Electricity usage data scraper for e-st.lv
    """

    BASE_HOST = 'https://www.e-st.lv'
    LOGIN_URL = BASE_HOST + '/lv/private/user-authentification/'
    DATA_URL = BASE_HOST + '/lv/private/paterini-un-norekini/paterinu-grafiki/'

    # Data url parameters

    PERIOD_DAY = 'D'
    PERIOD_MONTH = 'M'
    PERIOD_YEAR = 'Y'

    GRANULARITY_NATIVE = 'NATIVE'
    GRANULARITY_HOUR = 'H'
    GRANULARITY_DAY = 'D'

    def __init__(self, login, password, meter_id):
        """
        Class initialisation

        :param login: username
        :param password: user password
        :param meter_id: electricity meter ID
        """
        self.login = login
        self.password = password
        self.meter_id = meter_id

        self.session = requests.Session()

    @staticmethod
    def _format_now(options):
        """
        Format current datetime depending on formatting params

        :param options:
        :return:
        """
        return datetime.datetime.now().strftime(options)

    def _get_current_year(self):
        """
        Get the current year e.g. 2017
        """
        return self._format_now('%Y')

    def _get_current_month(self):
        """
        Get the current month e.g. 01
        """
        return self._format_now('%m')

    def _get_current_day(self):
        """
        Get the current day e.g. 01
        """
        return self._format_now('%d')

    def _get_data_url(self, period=None, year=None, month=None, day=None, granularity=None):
        """
        Prepare data url depending on request type and parameters

        :param period: report time period
        :type period: str | should be one of self.PERIOD_<*>
        :param year: year
        :type year: str | None
        :param month: month
        :type month: str | None
        :param day: day
        :type day: str | None
        :param granularity: report data type
        :type granularity: str | should be one of self.GRANULARITY_<*>

        :return: generated data url
        """

        params = {
            'counterNumber': self.meter_id,
            'period': period
        }

        year = year or self._get_current_year()

        if period == self.PERIOD_YEAR:
            params['year'] = year

        if period == self.PERIOD_MONTH:
            params['year'] = year
            params['month'] = month or self._get_current_month()
            params['granularity'] = granularity

        if period == self.PERIOD_DAY:

            month = month or self._get_current_month()
            day = day or self._get_current_day()

            params['date'] = '{0}.{1}.{2}'.format(day, month, year)
            params['granularity'] = granularity

        print(self.DATA_URL + '?' + urlencode(params))
        return self.DATA_URL + '?' + urlencode(params)

    @staticmethod
    def _format_timestamp(timestamp):
        """
        Convert JS timestamp to human readable date and time

        :param timestamp: timestamp
        :return: datetime e.g. 2016-03-01 02:00:00
        :rtype: str
        """
        return datetime.datetime.fromtimestamp(int(timestamp) / 1000.0).strftime('%Y-%m-%d %H:%M:%S')

    def _format_response(self, response_data):
        """
        Parse out the real data from graph json

        :param response_data: graph json source
        :return: parsed data
        """
        response_data = response_data['values']['A+']['total']['data']
        return [{
            'data': self._format_timestamp(item['timestamp']),
            'value': item['value']
        } for item in response_data]

    def get_day_data(self, year=None, month=None, day=None):
        """
        Get the data of the specified day

        :param year:
        :param month:
        :param day:
        :return:
        """
        response = self._fetch_remote_data(period=self.PERIOD_DAY, month=month,
                                           year=year, day=day,
                                           granularity=self.GRANULARITY_HOUR)
        return self._format_response(response)

    def get_month_data(self, year=None, month=None):
        """
        Get the data of the specified month

        :param year:
        :param month:
        :return:
        """
        response = self._fetch_remote_data(period=self.PERIOD_MONTH, month=month, year=year,
                                           granularity=self.GRANULARITY_DAY)
        return self._format_response(response)

    def get_year_data(self, year=None):
        """
        Get the data of the specified year

        :param year:
        :return:
        """
        response = self._fetch_remote_data(period=self.PERIOD_YEAR, year=year)
        return self._format_response(response)

    def _fetch_remote_data(self, **kwargs):
        """

        :param kwargs:
        :return:
        """
        # Read the "Please authenticate" page html source
        response = self.session.get(self._get_data_url(**kwargs))
        root = PyQuery(response.text)

        fields = (
            '_token',
            'returnUrl',
            'login',
            'password'
        )

        values = {}
        for field in fields:
            values[field] = root('input[name={0}]'.format(field)).attr('value')

        values['login'] = self.login
        values['password'] = self.password

        # Do the actual authentication
        response = self.session.post(self.LOGIN_URL, data=values)
        root = PyQuery(response.text)
        values = root('div.chart').attr('data-values')
        return json.loads(values)


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='www.e-st.lv usage data spider')
    parser.add_argument('--username', default=None, help='Website username')
    parser.add_argument('--password', default=None, help='Website password')
    parser.add_argument('--meter', default=None, help='Electricity meter ID')
    parser.add_argument('--period', default='month', help='Report data time period')
    parser.add_argument('--year', default=None)
    parser.add_argument('--month', default=None)
    parser.add_argument('--day', default=None)
    parser.add_argument('--outfile', default=None, help='Save data in specified file')

    opts = parser.parse_args()

    if not opts.username or not opts.password:
        raise Exception('Username and/or password must be set')

    if not opts.meter:
        raise Exception('Electricity meter ID must be set')

    scraper = ESTScraper(opts.username, opts.password, opts.meter)

    if opts.period == 'year':
        data = scraper.get_year_data(opts.year)

    if opts.period == 'month':
        data = scraper.get_month_data(opts.year, opts.month)

    if opts.period == 'day':
        data = scraper.get_day_data(opts.year, opts.month, opts.day)

    data = json.dumps(data, indent=4)

    if opts.outfile:
        f = open(opts.outfile, 'w')
        f.write(data)
        f.close()
    else:
        print(data)
