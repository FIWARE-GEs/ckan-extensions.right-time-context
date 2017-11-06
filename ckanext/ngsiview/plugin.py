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
    from ckan.common import _, request
    import ckanext.resourceproxy.plugin as proxy
except ImportError:
    pass


def check_query(resource):
    if resource['url'].lower().find('/querycontext') != -1 or resource['url'].lower().find('/contextentities/') != -1:
        return True
    else:
        return False


class NgsiView(p.SingletonPlugin):

    p.implements(p.IRoutes, inherit=True)
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IConfigurable, inherit=True)

    if p.toolkit.check_ckan_version(min_version='2.3'):
        p.implements(p.IResourceView, inherit=True)
    else:
        p.implements(p.IResourcePreview, inherit=True)

    NGSI_FORMATS = ['ngsi9','ngsi10','ngsi-h']

    def before_map(self, m):
        m.connect('/dataset/{id}/resource/{resource_id}/ngsiproxy',
        controller='ckanext.ngsiview.controller:ProxyNGSIController', action='proxy_ngsi_resource')
        return m

    def get_proxified_ngsi_url(self, data_dict):
        url = h.url_for(action='proxy_ngsi_resource', controller='ckanext.ngsiview.controller:ProxyNGSIController',
        id=data_dict['package']['name'], resource_id=data_dict['resource']['id'])
        log.info('Proxified url is {0}'.format(url))
        return url

    def update_config(self, config):
        # This function is only maintained to allow proper functioning of the extension
        # in ckan versions previous to ckan2.3
        p.toolkit.add_resource('theme/public', 'ckanext-ngsiview')
        p.toolkit.add_public_directory(config, 'theme/public')

    	if p.toolkit.check_ckan_version(min_version='2.3'):
            p.toolkit.add_template_directory(config, 'theme/templates')
        else:
            p.toolkit.add_template_directory(config, 'theme/templates/old_templates')

    def configure(self, config):
        self.proxy_is_enabled = config.get('ckan.resource_proxy_enabled')
        if config.get('ckan.plugins').find('oauth2') != -1:
            self.oauth2_is_enabled = True
        else:
            self.oauth2_is_enabled = False

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

        if format_lower in self.NGSI_FORMATS and check_query(resource):
            if check_query(resource):
                return not same_domain or proxy_enabled
            else:
                return False
        else:
            return False

    def can_preview(self, data_dict):
        # This function is only maintained to allow proper functioning of the extension
        # in ckan versions previous to ckan2.3
        resource = data_dict['resource']
        if 'oauth_req' not in resource:
            oauth_req = 'false'
        else:
            oauth_req = resource['oauth_req']

        format_lower = resource['format'].lower()
        if format_lower in self.NGSI_FORMATS:
            if self.proxy_is_enabled and not resource['on_same_domain'] and check_query(resource):
                if oauth_req == 'true' and not p.toolkit.c.user:
                    details = "In order to see this resource properly, you need to be logged in"
                    h.flash_error(details, allow_html=False)
                    return {'can_preview': False, 'fixable': details, 'quality': 2}
                elif oauth_req == 'true' and not self.oauth2_is_enabled:
                    details = "Enable oauth2 extension"
                    h.flash_error(details, allow_html=False)
                    return {'can_preview': False, 'fixable': details, 'quality': 2}
                elif (resource['url'].lower().find('/querycontext') != -1
                      and 'payload' not in resource):
                    details = "Add a payload to complete the query"
                    h.flash_error(details, allow_html=False)
                    return {'can_preview': False, 'fixable': details, 'quality': 2}
                else:
                    return {'can_preview': True, 'quality': 2}
            else:
                return {'can_preview': False}
        else:
            return {'can_preview': False}

    def setup_template_variables(self, context, data_dict):
    	if p.toolkit.check_ckan_version(min_version='2.3'):
            metadata = {'ngsi_formats': self.NGSI_FORMATS}
            resource = data_dict['resource']
            proxy_enabled = p.plugin_loaded('resource_proxy')
            oauth2_enabled = p.plugin_loaded('oauth2')
            same_domain = datapreview.on_same_domain(data_dict)

            if 'oauth_req' not in resource:
                oauth_req = 'false'
            else:
                oauth_req = resource['oauth_req']

            if proxy_enabled and not same_domain:
                if check_query(resource):
                    if oauth_req == 'true' and not p.toolkit.c.user:
                        details = "</br></br>In order to see this resource properly, you need to be logged in.</br></br></br>"
                        f_details = "In order to see this resource properly, you need to be logged in."
                        h.flash_error(f_details, allow_html=False)
                        view_enable = [False, details]
                        url = proxy.get_proxified_resource_url(data_dict)

                    elif oauth_req == 'true' and not oauth2_enabled:
                        details = "</br></br>In order to see this resource properly, enable oauth2 extension</br></br></br>"
                        f_details = "In order to see this resource properly, enable oauth2 extension."
                        h.flash_error(f_details, allow_html=False)
                        view_enable = [False, details]
                        url = proxy.get_proxified_resource_url(data_dict)

                    else:
                        url = self.get_proxified_ngsi_url(data_dict)
                        data_dict['resource']['url'] = url
                        view_enable = [True, 'OK']

                else:
                    details = "</br></br>This is not a ContextBroker query, please check <a href='https://forge.fiware.org/plugins/mediawiki/wiki/fiware/index.php/Publish/Subscribe_Broker_-_Orion_Context_Broker_-_User_and_Programmers_Guide'>Orion Context Broker documentation</a></br></br></br>"
                    f_details = "This is not a ContextBroker query, please check Orion Context Broker documentation."
                    h.flash_error(f_details, allow_html=False)
                    view_enable = [False, details]
                    url = proxy.get_proxified_resource_url(data_dict)
            else:
                if proxy_enabled:
                    details = "</br></br>Enable resource_proxy</br></br></br>"
                    f_details = "Enable resource_proxy."

                else:
                    details = "</br></br>This is not a ContextBroker query, please check <a href='https://forge.fiware.org/plugins/mediawiki/wiki/fiware/index.php/Publish/Subscribe_Broker_-_Orion_Context_Broker_-_User_and_Programmers_Guide'>Orion Context Broker documentation</a></br></br></br>"
                    f_details = "This is not a ContextBroker query, please check Orion Context Broker documentation."

                h.flash_error(f_details, allow_html=False)
                view_enable = [False, details]
                url = ''

            return {'preview_metadata': json.dumps(metadata),
                    'resource_json': json.dumps(data_dict['resource']),
                    'resource_url': json.dumps(url),
                    'view_enable': json.dumps(view_enable)}
        else:
            if self.proxy_is_enabled and not data_dict['resource']['on_same_domain']:
                if check_query(data_dict['resource']):
                    url = self.get_proxified_ngsi_url(data_dict)
                    p.toolkit.c.resource['url'] = url

    def view_template(self, context, data_dict):
        return 'ngsi.html'

    def preview_template(self, context, data_dict):
        # This function is only maintained to allow proper functioning of the extension
        # in ckan versions previous to ckan2.3
        return 'ngsi.html'
