#!/usr/bin/env python
# Copyright 2015 Telefonica Investigacion y Desarrollo, S.A.U
#
# This file is part of ckanext-ngsipreview.
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
# along with Orion Context Broker. If not, see http://www.gnu.org/licenses/.

import logging

from ckan.common import json
import ckan.plugins as p
import ckan.lib.helpers as h

log = logging.getLogger(__name__)

try:
    import ckan.lib.datapreview as datapreview
except ImportError:
    pass


NGSI_FORMAT = 'fiware-ngsi'


def check_query(resource):
    parsedurl = resource['url']
    return parsedurl.find('/v2/entities') != -1 or parsedurl.find('/v1/querycontext') != -1 or parsedurl.find('/v1/contextentities/') != -1


class NgsiView(p.SingletonPlugin):

    p.implements(p.IRoutes, inherit=True)
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IConfigurable, inherit=True)
    p.implements(p.IResourceView, inherit=True)

    def before_map(self, m):
        m.connect(
            '/dataset/{id}/resource/{resource_id}/ngsiproxy',
            controller='ckanext.ngsiview.controller:ProxyNGSIController',
            action='proxy_ngsi_resource'
        )
        return m

    def get_proxified_ngsi_url(self, data_dict):
        url = h.url_for(
            action='proxy_ngsi_resource',
            controller='ckanext.ngsiview.controller:ProxyNGSIController',
            id=data_dict['package']['name'],
            resource_id=data_dict['resource']['id']
        )
        log.info('Proxified url is {0}'.format(url))
        return url

    def configure(self, config):
        self.proxy_is_enabled = config.get('ckan.resource_proxy_enabled')
        self.oauth2_is_enabled = config.get('ckan.plugins').find('oauth2') != -1

    def info(self):
        return {'name': 'ngsiview',
                'title': p.toolkit._('NGSI'),
                'icon': 'file-text-o' if p.toolkit.check_ckan_version(min_version='2.7') else 'file-text-alt',
                'default_title': p.toolkit._('NGSI'),
                'default_description': 'NGSI resource',
                'always_available': False,
                'iframed': True,
                'preview_enabled': True,
                'full_page_edit': False,
                }

    def can_view(self, data_dict):
        resource = data_dict['resource']
        format_lower = resource.get('format', '').lower()
        proxy_enabled = p.plugin_loaded('resource_proxy')
        same_domain = datapreview.on_same_domain(data_dict)

        if format_lower == NGSI_FORMAT and check_query(resource):
            return same_domain or proxy_enabled
        else:
            return False

    def setup_template_variables(self, context, data_dict):
        resource = data_dict['resource']
        proxy_enabled = p.plugin_loaded('resource_proxy')
        oauth2_enabled = p.plugin_loaded('oauth2')
        same_domain = datapreview.on_same_domain(data_dict)

        if 'oauth_req' not in resource:
            oauth_req = 'false'
        else:
            oauth_req = resource['oauth_req']

        url = resource['url']
        if not check_query(resource):
            details = "</br></br>This is not a ContextBroker query, please check <a href='https://forge.fiware.org/plugins/mediawiki/wiki/fiware/index.php/Publish/Subscribe_Broker_-_Orion_Context_Broker_-_User_and_Programmers_Guide'>Orion Context Broker documentation</a></br></br></br>"
            f_details = "This is not a ContextBroker query, please check Orion Context Broker documentation."
            h.flash_error(f_details, allow_html=False)
            view_enable = [False, details]
        elif not same_domain and not proxy_enabled:
            details = "</br></br>Enable resource_proxy</br></br></br>"
            f_details = "Enable resource_proxy."
            h.flash_error(f_details, allow_html=False)
            view_enable = [False, details]
            url = ''
        else:
            if not same_domain:
                url = self.get_proxified_ngsi_url(data_dict)

            if oauth_req == 'true' and not p.toolkit.c.user:
                details = "</br></br>In order to see this resource properly, you need to be logged in.</br></br></br>"
                f_details = "In order to see this resource properly, you need to be logged in."
                h.flash_error(f_details, allow_html=False)
                view_enable = [False, details]

            elif oauth_req == 'true' and not oauth2_enabled:
                details = "</br></br>In order to see this resource properly, enable oauth2 extension</br></br></br>"
                f_details = "In order to see this resource properly, enable oauth2 extension."
                h.flash_error(f_details, allow_html=False)
                view_enable = [False, details]

            else:
                data_dict['resource']['url'] = url
                view_enable = [True, 'OK']

        return {
            'resource_json': json.dumps(data_dict['resource']),
            'resource_url': json.dumps(url),
            'view_enable': json.dumps(view_enable)
        }

    def view_template(self, context, data_dict):
        return 'ngsi.html'
