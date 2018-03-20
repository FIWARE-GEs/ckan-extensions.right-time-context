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

from mock import DEFAULT, patch
from parameterized import parameterized

import ckanext.ngsiview.plugin as plugin


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
    @patch.multiple('ckanext.ngsiview.plugin', datapreview=DEFAULT, p=DEFAULT)
    def test_can_view(self, resource_format, resource_url, same_domain, proxy_enabled, expected, datapreview, p):
        instance = plugin.NgsiView()
        datapreview.on_same_domain.return_value = same_domain
        p.plugin_loaded.return_value = proxy_enabled
        self.assertEqual(
            instance.can_view({'resource': {'format': resource_format, 'url': resource_url}}),
            expected
        )
