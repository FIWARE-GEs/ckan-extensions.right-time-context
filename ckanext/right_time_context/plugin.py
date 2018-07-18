#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2015 Telefonica Investigacion y Desarrollo, S.A.U
# Copyright 2018 CoNWeT Lab, Universidad Politécnica de Madrid
# Copyright (c) 2018 Future Internet Consulting and Development Solutions S.L.
#
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
# along with CKAN NGSI View extension. If not, see http://www.gnu.org/licenses/.

import logging

from ckan.common import _, json
import ckan.plugins as p
import ckan.lib.helpers as h

log = logging.getLogger(__name__)

try:
    import ckan.lib.datapreview as datapreview
except ImportError:
    pass


NGSI_FORMAT = 'fiware-ngsi'
NGSI_REG_FORMAT = 'fiware-ngsi-registry'


def check_query(resource):
    parsedurl = resource['url']
    return parsedurl.find('/v2/entities') != -1 or parsedurl.find('/v1/querycontext') != -1 or parsedurl.find('/v1/contextentities/') != -1


class NgsiView(p.SingletonPlugin):

    p.implements(p.IRoutes, inherit=True)
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IConfigurable, inherit=True)
    p.implements(p.IResourceView, inherit=True)
    p.implements(p.IResourceController, inherit=True)
    p.implements(p.ITemplateHelpers)

    def before_map(self, m):
        m.connect(
            '/dataset/{id}/resource/{resource_id}/ngsiproxy',
            controller='ckanext.right_time_context.controller:ProxyNGSIController',
            action='proxy_ngsi_resource'
        )
        return m

    def get_helpers(self):

        def get_available_auth_methods():
            auth_options = [
                {'value': 'none', 'text': _('None')},
            ]

            if self.oauth2_is_enabled:
                auth_options.extend([
                    {'value': 'oauth2', 'text': _('OAuth 2.0')},
                    {'value': 'x-auth-token-fiware', 'text': _('OAuth 2.0 token using X-Auth-Token (deprecated)')},
                ])

            return auth_options

        return {
            "right_time_context_get_available_auth_methods": get_available_auth_methods,
        }

    def get_proxified_ngsi_url(self, data_dict):
        url = h.url_for(
            action='proxy_ngsi_resource',
            controller='ckanext.right_time_context.controller:ProxyNGSIController',
            id=data_dict['package']['name'],
            resource_id=data_dict['resource']['id']
        )
        log.info('Proxified url is {0}'.format(url))
        return url

    def configure(self, config):
        self.proxy_is_enabled = p.plugin_loaded('resource_proxy')
        self.oauth2_is_enabled = p.plugin_loaded('oauth2')

    def update_config(self, config):
        p.toolkit.add_template_directory(config, 'templates')
        p.toolkit.add_resource('fanstatic', 'right_time_context')
        p.toolkit.add_public_directory(config, 'public')

    def info(self):
        return {
            'name': 'ngsi_view',
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
        same_domain = datapreview.on_same_domain(data_dict)

        if (format_lower == NGSI_FORMAT and check_query(resource)) or format_lower == NGSI_REG_FORMAT:
            return same_domain or self.proxy_is_enabled
        else:
            return False

    def setup_template_variables(self, context, data_dict):
        resource = data_dict['resource']
        same_domain = datapreview.on_same_domain(data_dict)
        format_lower = resource.get('format', '').lower()
        resource.setdefault('auth_type', 'none')

        url = resource['url']
        if format_lower == NGSI_FORMAT and not check_query(resource):
            details = "</br></br>This is not a ContextBroker query, please check <a href='https://forge.fiware.org/plugins/mediawiki/wiki/fiware/index.php/Publish/Subscribe_Broker_-_Orion_Context_Broker_-_User_and_Programmers_Guide'>Orion Context Broker documentation</a></br></br></br>"
            f_details = "This is not a ContextBroker query, please check Orion Context Broker documentation."
            h.flash_error(f_details, allow_html=False)
            view_enable = [False, details]
        elif not same_domain and not self.proxy_is_enabled:
            details = "</br></br>Enable resource_proxy</br></br></br>"
            f_details = "Enable resource_proxy."
            h.flash_error(f_details, allow_html=False)
            view_enable = [False, details]
            url = ''
        else:
            if not same_domain:
                url = self.get_proxified_ngsi_url(data_dict)

            if resource['auth_type'] != 'none' and not p.toolkit.c.user:
                details = "</br></br>In order to see this resource properly, you need to be logged in.</br></br></br>"
                f_details = "In order to see this resource properly, you need to be logged in."
                h.flash_error(f_details, allow_html=False)
                view_enable = [False, details]

            elif resource['auth_type'] != 'none' and not self.oauth2_is_enabled:
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

    def _iterate_serialized(self, resource, handler):
        pending_entities = True
        index = 0
        while pending_entities:
            prefix = 'entity__' + str(index) + '__'

            if prefix + 'id' in resource:
                handler(prefix)
                index = index + 1
            else:
                pending_entities = False

    def _serialize_resource(self, resource):
        # Check if NGSI resource is being created
        serialized_resource = resource
        if resource['format'] == NGSI_REG_FORMAT:

            if 'entity' not in resource or not len(resource['entity']):
                # Raise an error, al least one entity must be provided
                raise p.toolkit.ValidationError({'NGSI Data': ['At least one NGSI entity must be provided']})

            # Remove all serialized entries from the resource
            def remove_serialized(prefix):
                del resource[prefix + 'id']
                del resource[prefix + 'value']

                if prefix + 'isPattern' in resource:
                    del resource[prefix + 'isPattern']

            self._iterate_serialized(resource, remove_serialized)

            index = 0
            # Serialize entity information to support custom field saving
            entities = {}
            for entity in resource['entity']:
                if 'delete' in entity and entity['delete'] == 'on':
                    continue

                prefix = 'entity__' + str(index) + '__'
                entities[prefix + 'id'] = entity['id']
                entities[prefix + 'value'] = entity['value']

                # Check if there is an isPattern field
                if 'isPattern' in entity and entity['isPattern'] == 'on':
                    entities[prefix + 'isPattern'] = entity['isPattern']
                index = index + 1

            del serialized_resource['entity']
            serialized_resource.update(entities)

        return serialized_resource

    def before_create(self, context, resource):
        return self._serialize_resource(resource)

    def after_create(self, context, resource):
        # Create entry in the NGSI registry
        pass

    def before_update(self, context, current, resource):
        return self._serialize_resource(resource)

    def after_update(self, context, resource):
        pass

    def before_show(self, resource):
        # Deserialize resource information
        entities = []

        def deserilize_handler(prefix):
            entity = {
                'id': resource[prefix + 'id'],
                'value': resource[prefix + 'value'],
            }

            if prefix + 'isPattern' in resource:
                entity['isPattern'] = resource[prefix + 'isPattern']

            entities.append(entity)

        self._iterate_serialized(resource, deserilize_handler)

        resource['entity'] = entities

        return resource
