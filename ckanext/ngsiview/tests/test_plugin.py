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

import ckanext.ngsiview.plugin as plugin


class NgsiViewPluginTest(unittest.TestCase):

    def test_can_view_returns_false_unnamaged_format(self):
        instance = plugin.NgsiView()
        self.assertFalse(instance.can_view({'resource': {'format': 'CSV'}, }))
