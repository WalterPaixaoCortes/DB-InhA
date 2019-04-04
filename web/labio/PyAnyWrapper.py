# -*- coding: utf-8 -*-
"""
    Wrapper module for python anywhere api
"""
import traceback

import requests

# -------------------------------------------------------------------------------------------------
# Wrapper class for python anywhere api
# -------------------------------------------------------------------------------------------------
class PyAnyApi():
    """
        Class to interface with python anywhere api
    """
    __client = None
    __access_token = None
    __user_name = None

    __HOST = "https://www.pythonanywhere.com"
    __ENDPOINTS = {
        "create_schedule": "/api/v0/user/%s/schedule/",
        "get_schedules": "/api/v0/user/%s/schedule/"
    }
    __HEADERS = {
        "Authorization": None
    }

    def __init__(self, access_token, username, proxy=None):
        """
            Class constructor
        """
        self.__client = requests.session()
        if proxy:
            self.__client.proxies.update(proxy)
        self.__access_token = access_token
        self.__HEADERS['Authorization'] = "Token %s" % access_token
        self.__client.headers.update(self.__HEADERS)
        self.__user_name = username

    def get_from_url(self, url, param=None):
        """
            return generic json from generic url
        """
        response = self.__client.get(url % self.__user_name, params=param)
        response_json = response.json()
        return response_json

    def post_from_url(self, url, param=None):
        """
            return generic json from generic url
        """
        response = self.__client.post(url % self.__user_name, data=param)
        response_json = response.json()
        return response_json

    def get_schedules(self, param=None):
        """
            return list of scheduled tasks
        """
        uri = "%s%s" % (self.__HOST, self.__ENDPOINTS[self.get_schedules.__name__])
        return self.get_from_url(uri, param)

    def create_schedule(self, param=None):
        """
            create a new schedule
        """
        uri = "%s%s" % (self.__HOST, self.__ENDPOINTS[self.create_schedule.__name__])
        return self.post_from_url(uri, param)
