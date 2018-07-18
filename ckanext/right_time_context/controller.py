#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2015 Telefonica Investigacion y Desarrollo, S.A.U
# Copyright 2018 CoNWeT Lab. Univerisdad Politécnica de Madrid
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
# along with Orion Context Broker. If not, see http://www.gnu.org/licenses/.

import json
from logging import getLogger
import os
import urlparse

import ckan.logic as logic
import ckan.lib.base as base
from ckan.plugins import toolkit
import requests
import six

from .plugin import NGSI_REG_FORMAT

log = getLogger(__name__)

CHUNK_SIZE = 512


class ProxyNGSIController(base.BaseController):

    def _proxy_query_resource(self, resource, parsed_url, headers, verify=True):

        if parsed_url.path.find('/v1/queryContext') != -1:
            if resource.get("payload", "").strip() == "":
                details = 'Please add a payload to complete the query.'
                base.abort(409, detail=details)

            try:
                json.loads(resource['payload'])
            except json.JSONDecodeError:
                details = "Payload field doesn't contain valid JSON data."
                base.abort(409, detail=details)

            headers['Content-Type'] = "application/json"
            r = requests.post(resource['url'], headers=headers, data=resource["payload"], stream=True, verify=verify)

        else:
            r = requests.get(resource['url'], headers=headers, stream=True, verify=verify)

        return r

    def _proxy_registration_resource(self, resource, parsed_url, headers, verify=True):
        path = parsed_url.path

        if path.endswith('/'):
            path = path[:-1]

        path = path + '/v2/op/query'
        attrs = []

        if 'attrs_str' in resource and len(resource['attrs_str']):
            attrs = resource['attrs_str'].split(',')
        body = {
            'entities': [],
            'attrs': attrs
        }

        # Include entity information
        for entity in resource['entity']:
            query_entity = {
                'type': entity['value']
            }
            if 'isPattern' in entity and entity['isPattern'] == 'on':
                query_entity['idPattern'] = entity['id']
            else:
                query_entity['id'] = entity['id']

            body['entities'].append(query_entity)

        # Parse expression to include georel information
        if 'expression' in resource and len(resource['expression']):
            # Separate expresion query strings
            supported_expressions = ['georel', 'geometry', 'coords']
            parsed_expression = resource['expression'].split('&')

            expression = {}
            for exp in parsed_expression:
                parsed_exp = exp.split('=')

                if len(parsed_exp) != 2 or not parsed_exp[0] in supported_expressions:
                    base.abort(422, detail='The expression is not a valid one for NGSI Registration, only georel, geometry, and coords is supported')
                else:
                    expression[parsed_exp[0]] = parsed_exp[1]

            body['expression'] = expression

        headers['Content-Type'] = 'application/json'
        url = urlparse.urljoin(parsed_url.scheme + '://' + parsed_url.netloc, path)
        response = requests.post(url, headers=headers, json=body, stream=True, verify=verify)

        return response

    def process_auth_credentials(self, resource, headers):
        auth_method = resource.get('auth_type', 'none')

        if auth_method == "oauth2":
            token = toolkit.c.usertoken['access_token']
            headers['Authorization'] = "Bearer %s" % token
        elif auth_method == "x-auth-token-fiware":
            # Deprecated method, Including OAuth2 token retrieved from the IdM
            # on the Open Stack X-Auth-Token header
            token = toolkit.c.usertoken['access_token']
            headers['X-Auth-Token'] = token

    def proxy_ngsi_resource(self, resource_id):
        # Chunked proxy for ngsi resources.
        context = {'model': base.model, 'session': base.model.Session, 'user': base.c.user or base.c.author}

        log.info('Proxify resource {id}'.format(id=resource_id))
        resource = logic.get_action('resource_show')(context, {'id': resource_id})

        headers = {
            'Accept': 'application/json'
        }

        resource.setdefault('auth_type', 'none')
        self.process_auth_credentials(resource, headers)

        if resource.get('tenant', '') != '':
            headers['FIWARE-Service'] = resource['tenant']
        if resource.get('service_path', '') != '':
            headers['FIWARE-ServicePath'] = resource['service_path']

        url = resource['url']
        parsed_url = urlparse.urlsplit(url)

        if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
            base.abort(409, detail='Invalid URL.')

        # Process verify configuration
        verify_conf = os.environ.get('CKAN_RIGHT_TIME_CONTEXT_VERIFY_REQUESTS', toolkit.config.get('ckan.right_time_context.verify_requests'))
        if verify_conf is None or (isinstance(verify_conf, six.string_types) and verify_conf.strip() == ""):
            verify_conf = os.environ.get('CKAN_VERIFY_REQUESTS', toolkit.config.get('ckan.verify_requests'))

        if isinstance(verify_conf, six.string_types) and verify_conf.strip() != "":
            compare_env = verify_conf.lower().strip()
            if compare_env in ("true", "1", "on"):
                verify = True
            elif compare_env in ("false", "0", "off"):
                verify = False
            else:
                verify = verify_conf
        elif isinstance(verify_conf, bool):
            verify = verify_conf
        else:
            verify = True

        # Make the request to the server
        try:
            if resource['format'].lower() == NGSI_REG_FORMAT:
                r = self._proxy_registration_resource(resource, parsed_url, headers, verify=verify)
            else:
                r = self._proxy_query_resource(resource, parsed_url, headers, verify=verify)

        except requests.HTTPError:
            details = 'Could not proxy ngsi_resource. We are working to resolve this issue as quickly as possible'
            base.abort(409, detail=details)
        except requests.ConnectionError:
            details = 'Could not proxy ngsi_resource because a connection error occurred.'
            base.abort(502, detail=details)
        except requests.Timeout:
            details = 'Could not proxy ngsi_resource because the connection timed out.'
            base.abort(504, detail=details)

        if r.status_code == 401:
            if resource.get('auth_type', 'none') != 'none':
                details = 'ERROR 401 token expired. Retrieving new token, reload please.'
                log.info(details)
                toolkit.c.usertoken_refresh()
                base.abort(409, detail=details)
            elif resource.get('auth_type', 'none') == 'none':
                details = 'Authentication requested by server, please check resource configuration.'
                log.info(details)
                base.abort(409, detail=details)

        elif r.status_code == 400:
            response = r.json()
            details = response['description']
            log.info(details)
            base.abort(422, detail=details)

        else:
            r.raise_for_status()
            base.response.content_type = r.headers['content-type']
            base.response.charset = r.encoding

        for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
            base.response.body_file.write(chunk)
