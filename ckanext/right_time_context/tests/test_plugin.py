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

import json
import unittest

from mock import ANY, DEFAULT, patch
from parameterized import parameterized

from ckan.plugins.toolkit import ValidationError

import ckanext.right_time_context.plugin as plugin


class NgsiViewPluginTest(unittest.TestCase):

    @parameterized.expand([
        ('CSV', '', False, False),
        ('CSV', '', True, False),
        ('fiware-ngsi', 'https://cb.example.com/v2/entities', False, False),
        ('FIWARE-ngsi', 'https://cb.example.com/v2/entities', False, False),
        ('FIWARE-ngsi', 'https://cb.example.com/v2/entities', True, True),
        ('FIWARE-ngsi', 'https://cb.example.com/other/path', False, False),
        ('fiware-ngsi', 'https://cb.example.com/other/path', True, False),
    ])
    @patch.multiple('ckanext.right_time_context.plugin', p=DEFAULT)
    def test_can_view(self, resource_format, resource_url, proxy_enabled, expected, p):
        instance = plugin.NgsiView()
        instance.proxy_is_enabled = proxy_enabled
        self.assertEqual(
            instance.can_view({'resource': {'format': resource_format, 'url': resource_url}}),
            expected
        )

    @parameterized.expand([
        ({'format': 'fiware-ngsi-registry', 'entity': [{'id': '.*', 'value': 'Room', 'isPattern': 'on'}, {'id': 'vehicle1', 'value': 'Vehicle'}]},
            {'format': 'fiware-ngsi-registry', 'entity__0__id': '.*', 'entity__0__value': 'Room', 'entity__0__isPattern': 'on',
                'entity__1__id': 'vehicle1', 'entity__1__value': 'Vehicle'}),
        ({'format': 'fiware-ngsi'}, {'format': 'fiware-ngsi'})
    ])
    def test_before_create(self, resource, serialized):
        instance = plugin.NgsiView()

        result = instance.before_create({}, resource)
        self.assertEquals(serialized, result)

    def test_before_create_missing_entity(self):
        instance = plugin.NgsiView()

        with self.assertRaises(ValidationError):
            instance.before_create({}, {'format': 'fiware-ngsi-registry'})

    @parameterized.expand([
        ({'format': 'fiware-ngsi-registry', 'entity': [{'id': '.*', 'value': 'Room', 'isPattern': 'on', 'delete': 'on'}, {'id': 'vehicle5', 'value': 'Vehicle'}],
            'entity__0__id': '.*', 'entity__0__value': 'Room', 'entity__0__isPattern': 'on', 'entity__1__id': 'vehicle1', 'entity__1__value': 'Vehicle'},
            {'format': 'fiware-ngsi-registry', 'entity__0__id': 'vehicle5', 'entity__0__value': 'Vehicle'})
    ])
    def test_before_update(self, resource, serialized):
        instance = plugin.NgsiView()

        result = instance.before_update({}, {}, resource)
        self.assertEquals(serialized, result)

    @parameterized.expand([
        ({'format': 'fiware-ngsi-registry', 'entity__0__id': '.*', 'entity__0__value': 'Room', 'entity__0__isPattern': 'on',
                'entity__1__id': 'vehicle1', 'entity__1__value': 'Vehicle'},
            {'format': 'fiware-ngsi-registry', 'entity__0__id': '.*', 'entity__0__value': 'Room', 'entity__0__isPattern': 'on',
                'entity__1__id': 'vehicle1', 'entity__1__value': 'Vehicle', 'entity': [{'id': '.*', 'value': 'Room', 'isPattern': 'on'},
                    {'id': 'vehicle1', 'value': 'Vehicle'}]})
    ])
    def test_before_show(self, resource, deserialized):
        instance = plugin.NgsiView()

        instance.before_show(resource)
        self.assertEquals(deserialized, resource)

    @parameterized.expand([
        ["fiware-ngsi",          "https://context.example.org/v2/entities",               "none",   None],
        ["fiware-ngsi",          "https://context.example.org/v1/queryContext",           "none",   None],
        #TODO ["fiware-ngsi",          "https://context.example.org/v1/contextEntities",        "none",   None],
        ["fiware-ngsi",          "https://context.example.org/v1/contextEntities/Entity", "none",   None],
        ["fiware-ngsi",          "https://context.example.org/v2/entities",               "none",   "noproxy"],
        ["fiware-ngsi",          "https://context.example.org/v2/entities",               "oauth2", "nooauth2"],
        ["fiware-ngsi",          "https://context.example.org/other/path",                "none",   "noquery"],
        ["fiware-ngsi",          "https://context.example.org/v2/entities",               "oauth2", "nologged"],
        ["fiware-ngsi-registry", "https://context.example.org/",                          "none",   None],
        ["fiware-ngsi-registry", "https://context.example.org/",                          "none",   "noproxy"],
        ["fiware-ngsi-registry", "https://context.example.org/",                          "oauth2", "nooauth2"],
        ["fiware-ngsi-registry", "https://context.example.org/",                          "oauth2", "nologged"],
    ])
    @patch.multiple('ckanext.right_time_context.plugin', p=DEFAULT, h=DEFAULT)
    def test_setup_template_variables(self, resource_format, url, auth_type, error, p, h):
        instance = plugin.NgsiView()
        data_dict = {
            "resource": {
                "auth_type": auth_type,
                "format": resource_format,
                "url": url,
            }
        }
        instance.proxy_is_enabled = error != "noproxy"
        instance.oauth2_is_enabled = error != "nooauth2"
        p.toolkit.c.user = error != "nologged"

        with patch.object(instance, "get_proxified_ngsi_url", return_value="proxied_url"):
            result = instance.setup_template_variables(None, data_dict)

        view_enable = json.loads(result['view_enable'])
        self.assertEqual(result['resource_json'], json.dumps(data_dict['resource']))

        if error is None:
            self.assertEqual(view_enable, [True, 'OK'])
            self.assertEqual(result['resource_url'], '"proxied_url"')
        else:
            h.flash_error.assert_called_with(ANY, allow_html=False)
            self.assertFalse(view_enable[0])
            self.assertNotEqual(view_enable[1], 'OK')
