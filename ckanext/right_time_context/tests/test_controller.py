# -*- coding: utf-8 -*-

# Copyright (c) 2018 Future Internet Consulting and Development Solutions S.L.

# This file is part of ckanext-right_time_context.
#
# Ckanext-right_time_context is free software: you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Ckanext-right_time_context is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with ckanext-right_time_context. If not, see http://www.gnu.org/licenses/.

import unittest

from mock import ANY, DEFAULT, patch
from parameterized import parameterized

from ckanext.right_time_context.controller import ProxyNGSIController


class NgsiViewControllerTestCase(unittest.TestCase):

    REGISTRY_RESOURCE = {
        'format': 'fiware-ngsi-registry',
        'url': 'http://cb.example.org',
        'entity': [{'id': '.*', 'value': 'Room', 'isPattern': 'on'}, {'id': 'vehicle1', 'value': 'Vehicle'}],
        'attrs_str': 'temperature,speed',
        'expression': 'georel=near;minDistance:5000&geometry=point&coords=-40.4,-3.5'
    }

    REGISTRY_QUERY = {
        'entities': [{'idPattern': '.*', 'type': 'Room'}, {'id': 'vehicle1', 'type': 'Vehicle'}],
        'attrs': ['temperature', 'speed'],
        'expression': {
            'georel': 'near;minDistance:5000',
            'geometry': 'point',
            'coords': '-40.4,-3.5'
        }
    }

    @classmethod
    def setUpClass(cls):
        super(NgsiViewControllerTestCase, cls).setUpClass()
        cls.controller = ProxyNGSIController()

    def _mock_response(self, req_method):
        body = '{"json": "body"}'
        response = req_method
        response.status_code = 200
        response.headers['content-type'] = "application/json"
        response.encoding = "UTF-8"
        response.iter_content.return_value = (body,)
        return response, body

    @parameterized.expand([
        ({"format": "fiware-ngsi"}, {}),
        ({"auth_type": "x-auth-token-fiware", 'format': 'fiware-ngsi'}, {"X-Auth-Token": "valid-access-token"}),
        ({"auth_type": "oauth2", 'format': 'fiware-ngsi'}, {"Authorization": "Bearer valid-access-token"}),
        ({"tenant": "a", 'format': 'fiware-ngsi'}, {"FIWARE-Service": "a"}),
        ({"service_path": "/a", 'format': 'fiware-ngsi'}, {"FIWARE-ServicePath": "/a"}),
        ({"tenant": "a", "service_path": "/a,/b", 'format': 'fiware-ngsi'}, {"FIWARE-Service": "a", "FIWARE-ServicePath": "/a,/b"}),
    ])
    @patch.multiple("ckanext.right_time_context.controller", base=DEFAULT, logic=DEFAULT, requests=DEFAULT, toolkit=DEFAULT, os=DEFAULT)
    def test_basic_request(self, resource, headers, base, logic, requests, toolkit, os):
        resource['url'] = "http://cb.example.org/v2/entites"
        logic.get_action('resource_show').return_value = resource
        response, body = self._mock_response(requests.get())
        os.environ = {
            "CKAN_VERIFY_REQUESTS": "true",
        }

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
        (REGISTRY_RESOURCE, REGISTRY_QUERY, {}),
        ({
            'format': 'fiware-ngsi-registry',
            'url': 'http://cb.example.org',
            'entity': [{'id': 'vehicle1', 'value': 'Vehicle'}],
            'expression': '',
            'attrs_str': ''
        }, {
            'entities': [{'id': 'vehicle1', 'type': 'Vehicle'}],
            'attrs': [],
        }, {})
    ])
    @patch.multiple("ckanext.right_time_context.controller", base=DEFAULT, logic=DEFAULT, requests=DEFAULT, toolkit=DEFAULT, os=DEFAULT)
    def test_registration_request(self, resource, query, headers, base, logic, requests, toolkit, os):
        logic.get_action('resource_show').return_value = resource
        response, body = self._mock_response(requests.post())
        os.environ = {
            "CKAN_VERIFY_REQUESTS": "true",
        }

        toolkit.c.usertoken = {
            'access_token': "valid-access-token",
        }

        expected_headers = {
            "Accept": "application/json",
            'Content-Type': 'application/json'
        }
        expected_headers.update(headers)

        self.controller.proxy_ngsi_resource("resource_id")

        url = resource['url'] + '/v2/op/query'
        requests.post.assert_called_with(url, headers=expected_headers, json=query, stream=True, verify=True)
        base.response.body_file.write.assert_called_with(body)

    @patch.multiple("ckanext.right_time_context.controller", base=DEFAULT, logic=DEFAULT, requests=DEFAULT, toolkit=DEFAULT, os=DEFAULT)
    def test_invalid_expression(self, base, logic, requests, toolkit, os):
        resource = {
            'format': 'fiware-ngsi-registry',
            'url': 'http://cb.example.org',
            'entity': [{'id': 'vehicle1', 'value': 'Vehicle'}],
            'attrs_str': '',
            'expression': 'invalid=near;minDistance:5000'
        }
        os.environ = {
            "CKAN_VERIFY_REQUESTS": "true",
        }

        toolkit.c.usertoken = {
            'access_token': "valid-access-token",
        }

        logic.get_action('resource_show').return_value = resource

        self.controller.proxy_ngsi_resource("resource_id")
        base.abort.assert_called_with(422, detail='The expression is not a valid one for NGSI Registration, only georel, geometry, and coords is supported')

    @patch.multiple("ckanext.right_time_context.controller", base=DEFAULT, logic=DEFAULT, requests=DEFAULT, toolkit=DEFAULT, os=DEFAULT)
    def test_invalid_reg_query(self, base, logic, requests, toolkit, os):
        logic.get_action('resource_show').return_value = self.REGISTRY_RESOURCE
        response, body = self._mock_response(requests.post())
        os.environ = {
            "CKAN_VERIFY_REQUESTS": "true",
        }

        err_msg = 'Error in the CB'
        response.status_code = 400
        response.json.return_value = {'description': err_msg}

        self.controller.proxy_ngsi_resource("resource_id")
        base.abort.assert_called_with(422, detail=err_msg)

    @parameterized.expand([
        ("",),
        ("relative/url",),
        ("http://#a",),
        ("ftp://example.com",),
        ("tatata:///da",),
    ])
    @patch.multiple("ckanext.right_time_context.controller", base=DEFAULT, logic=DEFAULT, requests=DEFAULT, toolkit=DEFAULT, os=DEFAULT)
    def test_invalid_url_request(self, url, base, logic, requests, toolkit, os=DEFAULT):
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
    @patch.multiple("ckanext.right_time_context.controller", base=DEFAULT, logic=DEFAULT, requests=DEFAULT, toolkit=DEFAULT, os=DEFAULT)
    def test_auth_required_request(self, auth_configured, base, logic, requests, toolkit, os):
        resource = {
            'url': "http://cb.example.org/v2/entites",
            'auth_type': 'oauth2' if auth_configured else 'none',
            'format': 'fiware-ngsi'
        }
        logic.get_action('resource_show').return_value = resource
        response = requests.get()
        response.status_code = 401
        requests.get.reset_mock()
        base.abort.side_effect = TypeError
        os.environ = {
            "CKAN_VERIFY_REQUESTS": "true",
        }

        with self.assertRaises(TypeError):
            self.controller.proxy_ngsi_resource("resource_id")

        base.abort.assert_called_once_with(409, detail=ANY)
        requests.get.assert_called_once_with(resource['url'], headers=ANY, stream=True, verify=True)
        if auth_configured:
            toolkit.c.usertoken_refresh.assert_called_with()
        else:
            toolkit.c.usertoken_refresh.assert_not_called()

    @parameterized.expand([
        ("HTTPError", 409),
        ("ConnectionError", 502),
        ("Timeout", 504),
    ])
    @patch.multiple("ckanext.right_time_context.controller", base=DEFAULT, logic=DEFAULT, requests=DEFAULT, toolkit=DEFAULT, os=DEFAULT)
    def test_auth_required_request(self, exception, status_code, base, logic, requests, toolkit, os):
        resource = {
            'url': "http://cb.example.org/v2/entites",
            'format': 'fiware-ngsi'
        }
        logic.get_action('resource_show').return_value = resource
        setattr(requests, exception, ValueError)
        requests.get.side_effect = getattr(requests, exception)
        base.abort.side_effect = TypeError

        with self.assertRaises(TypeError):
            self.controller.proxy_ngsi_resource("resource_id")

        base.abort.assert_called_once_with(status_code, detail=ANY)
        requests.get.assert_called_once_with(resource['url'], headers=ANY, stream=True, verify=True)

    @parameterized.expand([
        ({}, {}, True),
        ({"CKAN_RIGHT_TIME_CONTEXT_VERIFY_REQUESTS": " "}, {}, True),
        ({"CKAN_VERIFY_REQUESTS": " "}, {}, True),
        ({}, {"ckan.verify_requests": False}, False),
        ({}, {"ckan.right_time_context.verify_requests": False}, False),
        ({}, {"ckan.right_time_context.verify_requests": False, "ckan.verify_requests": True}, False),
        ({"CKAN_VERIFY_REQUESTS": "false"}, {"ckan.verify_requests": True}, False),
        ({"CKAN_RIGHT_TIME_CONTEXT_VERIFY_REQUESTS": "True"}, {"ckan.verify_requests": False}, True),
        ({"CKAN_RIGHT_TIME_CONTEXT_VERIFY_REQUESTS": "True"}, {"ckan.right_time_context.verify_requests": False}, True),
        ({"CKAN_RIGHT_TIME_CONTEXT_VERIFY_REQUESTS": "true", "CKAN_VERIFY_REQUESTS": "false"}, {"ckan.verify_requests": False}, True),
        ({"CKAN_RIGHT_TIME_CONTEXT_VERIFY_REQUESTS": "on"}, {"ckan.verify_requests": False}, True),
        ({"CKAN_RIGHT_TIME_CONTEXT_VERIFY_REQUESTS": "1"}, {"ckan.verify_requests": False}, True),
        ({"CKAN_RIGHT_TIME_CONTEXT_VERIFY_REQUESTS": "off"}, {"ckan.verify_requests": True}, False),
        ({"CKAN_RIGHT_TIME_CONTEXT_VERIFY_REQUESTS": "0"}, {"ckan.verify_requests": True}, False),
        ({"CKAN_RIGHT_TIME_CONTEXT_VERIFY_REQUESTS": "/path"}, {"ckan.verify_requests": True}, "/path"),
        ({"CKAN_RIGHT_TIME_CONTEXT_VERIFY_REQUESTS": " "}, {"ckan.verify_requests": False}, False),
        ({"CKAN_VERIFY_REQUESTS": "/path/A/b"}, {"ckan.verify_requests": "path/2"}, "/path/A/b"),
    ])
    @patch.multiple("ckanext.right_time_context.controller", base=DEFAULT, logic=DEFAULT, requests=DEFAULT, toolkit=DEFAULT, os=DEFAULT)
    def test_verify_requests(self, env, config, expected_value, base, logic, requests, toolkit, os):
        logic.get_action('resource_show').return_value = {
            'url': "https://cb.example.org/v2/entites",
            'format': 'fiware-ngsi'
        }
        os.environ = env
        toolkit.config = config

        with patch.object(self.controller, '_proxy_query_resource') as query_mock:
            self.controller.proxy_ngsi_resource("resource_id")
            query_mock.assert_called_once_with(ANY, ANY, ANY, verify=expected_value)
