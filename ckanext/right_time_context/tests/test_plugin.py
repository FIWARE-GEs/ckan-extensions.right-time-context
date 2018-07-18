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

from mock import DEFAULT, patch
from parameterized import parameterized

from ckan.plugins.toolkit import ValidationError

import ckanext.right_time_context.plugin as plugin


class NgsiViewPluginTest(unittest.TestCase):

    @parameterized.expand([
        ('CSV', '', False, False, False),
        ('CSV', '', False, True, False),
        ('CSV', '', True, False, False),
        ('fiware-ngsi', 'https://cb.example.com/v2/entities', True, False, True),
        ('FIWARE-ngsi', 'https://cb.example.com/v2/entities', True, False, True),
        ('fiware-ngsi', 'https://cb.example.com/v2/entities', False, False, False),
        ('FIWARE-ngsi', 'https://cb.example.com/v2/entities', False, True, True),
        ('FIWARE-ngsi', 'https://cb.example.com/othe/path', True, False, False),
    ])
    @patch.multiple('ckanext.right_time_context.plugin', datapreview=DEFAULT, p=DEFAULT)
    def test_can_view(self, resource_format, resource_url, same_domain, proxy_enabled, expected, datapreview, p):
        instance = plugin.NgsiView()
        datapreview.on_same_domain.return_value = same_domain
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
