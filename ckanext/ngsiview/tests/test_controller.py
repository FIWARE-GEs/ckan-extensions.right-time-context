# -*- coding: utf-8 -*-

# Copyright (c) 2018 Future Internet Consulting and Development Solutions S.L.

# This file is part of ckanext-ngsiview.
#
# Ckanext-ngsiview is free software: you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Ckanext-ngsiview is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with ckanext-ngsiview. If not, see http://www.gnu.org/licenses/.

import unittest

from mock import ANY, DEFAULT, patch
from parameterized import parameterized

from ckanext.ngsiview.controller import ProxyNGSIController


class NgsiViewControllerTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(NgsiViewControllerTestCase, cls).setUpClass()
        cls.controller = ProxyNGSIController()

    @parameterized.expand([
        ({}, {}),
        ({"oauth_req": "true"}, {"X-Auth-Token": "valid-access-token"}),
        ({"tenant": "a"}, {"FIWARE-Service": "a"}),
        ({"service_path": "/a"}, {"FIWARE-ServicePath": "/a"}),
        ({"tenant": "a", "service_path": "/a,/b"}, {"FIWARE-Service": "a", "FIWARE-ServicePath": "/a,/b"}),
    ])
    @patch.multiple("ckanext.ngsiview.controller", base=DEFAULT, logic=DEFAULT, requests=DEFAULT, toolkit=DEFAULT)
    def test_basic_request(self, resource, headers, base, logic, requests, toolkit):
        body = '{"json": "body"}'
        resource['url'] = "http://cb.example.org/v2/entites"
        logic.get_action('resource_show').return_value = resource
        response = requests.get()
        response.status_code = 200
        response.headers['content-type'] = "application/json"
        response.encoding = "UTF-8"
        response.iter_content.return_value = (body,)
        toolkit.c.usertoken = {
            'access_token': "valid-access-token",
        }

        expected_headers = {
            "Accept": "application/json",
        }
        expected_headers.update(headers)

        self.controller.proxy_ngsi_resource("resource_id")

        requests.get.assert_called_with(resource['url'], headers=expected_headers, stream=True, verify=True)
        base.response.body_file.write.assert_called_with(body)

    @parameterized.expand([
        ("",),
        ("relative/url",),
        ("http://#a",),
        ("ftp://example.com",),
        ("tatata:///da",),
    ])
    @patch.multiple("ckanext.ngsiview.controller", base=DEFAULT, logic=DEFAULT, requests=DEFAULT, toolkit=DEFAULT)
    def test_invalid_url_request(self, url, base, logic, requests, toolkit):
        resource = {
            'url': url,
        }
        logic.get_action('resource_show').return_value = resource
        base.abort.side_effect = TypeError

        with self.assertRaises(TypeError):
            self.controller.proxy_ngsi_resource("resource_id")

        base.abort.assert_called_with(409, detail=ANY)
        requests.get.assert_not_called()

    @parameterized.expand([
        (True,),
        (False,),
    ])
    @patch.multiple("ckanext.ngsiview.controller", base=DEFAULT, logic=DEFAULT, requests=DEFAULT, toolkit=DEFAULT)
    def test_auth_required_request(self, auth_configured, base, logic, requests, toolkit):
        resource = {
            'url': "http://cb.example.org/v2/entites",
            'oauth_req': 'true' if auth_configured else 'false'
        }
        logic.get_action('resource_show').return_value = resource
        response = requests.get()
        response.status_code = 401
        requests.get.reset_mock()
        base.abort.side_effect = TypeError

        with self.assertRaises(TypeError):
            self.controller.proxy_ngsi_resource("resource_id")

        base.abort.assert_called_once_with(409, detail=ANY)
        requests.get.assert_called_once_with(resource['url'], headers=ANY, stream=True, verify=True)
        if auth_configured:
            toolkit.c.usertoken_refresh.assert_called_with()
        else:
            toolkit.c.usertoken_refresh.assert_not_called()
