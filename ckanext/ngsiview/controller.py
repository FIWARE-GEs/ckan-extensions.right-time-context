#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2015 Telefonica Investigacion y Desarrollo, S.A.U
# Copyright 2018 CoNWeT Lab. Univerisdad Politécnica de Madrid
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

from logging import getLogger
import urlparse
from pylons import config
import requests
import json
import ckan.logic as logic
import ckan.lib.base as base
import ckan.plugins as p

from .plugin import NGSI_REG_FORMAT

log = getLogger(__name__)

CHUNK_SIZE = 512


def proxy_query_resource(resource, parsed_url, headers):
    verify = config.get('ckan.ngsi.verify_requests', True)

    if parsed_url.path.find('/v1/queryContext') != -1:
        if resource.get("payload", "").strip() == "":
            details = 'Please add a payload to complete the query.'
            base.abort(409, detail=details)

        try:
            json.loads(resource['payload'])
        except:
            details = "Payload field doesn't contain valid JSON data."
            base.abort(409, detail=details)

        headers['Content-Type'] = "application/json"
        r = requests.post(resource['url'], headers=headers, data=resource["payload"], stream=True, verify=verify)

    else:
        r = requests.get(resource['url'], headers=headers, stream=True, verify=verify)

    return r


def proxy_registration_resource(resource, parsed_url, headers):
    verify = config.get('ckan.ngsi.verify_requests', True)
    path = parsed_url.path

    if path.endswith('/'):
        path = path[:-1]

    path = path + '/v2/op/query'
    body = {
        'entities': [],
        'attrs': resource['attrs_str'].split(',')
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


def proxy_ngsi_resource(context, data_dict):
    # Chunked proxy for ngsi resources.
    resource_id = data_dict['resource_id']
    log.info('Proxify resource {id}'.format(id=resource_id))
    resource = logic.get_action('resource_show')(context, {'id': resource_id})

    headers = {
        'Accept': 'application/json'
    }

    if 'oauth_req' in resource and resource['oauth_req'] == 'true':
        token = p.toolkit.c.usertoken['access_token']
        headers['X-Auth-Token'] = token

    if resource.get('tenant', '') != '':
        headers['FIWARE-Service'] = resource['tenant']
    if resource.get('service_path', '') != '':
        headers['FIWARE-ServicePath'] = resource['service_path']

    try:
        url = resource['url']
        try:
            parsed_url = urlparse.urlsplit(url)
        except:
            base.abort(409, detail='Invalid URL.')

        if not parsed_url.scheme or not parsed_url.netloc:
            base.abort(409, detail='Invalid URL.')

        if resource['format'].lower() == NGSI_REG_FORMAT:
            r = proxy_registration_resource(resource, parsed_url, headers)
        else:
            r = proxy_query_resource(resource, parsed_url, headers)

        if r.status_code == 401:
            if 'oauth_req' in resource and resource['oauth_req'] == 'true':
                details = 'ERROR 401 token expired. Retrieving new token, reload please.'
                log.info(details)
                base.abort(409, detail=details)
                p.toolkit.c.usertoken_refresh()

            elif 'oauth_req' not in resource or resource['oauth_req'] == 'false':
                details = 'This query may need Oauth-token, please check if the token field on resource_edit is correct.'
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

    except ValueError:
        details = ''
        base.abort(409, detail=details)
    except requests.HTTPError:
        details = 'Could not proxy ngsi_resource. We are working to resolve this issue as quickly as possible'
        base.abort(409, detail=details)
    except requests.ConnectionError:
        details = 'Could not proxy ngsi_resource because a connection error occurred.'
        base.abort(502, detail=details)
    except requests.Timeout:
        details = 'Could not proxy ngsi_resource because the connection timed out.'
        base.abort(504, detail=details)


class ProxyNGSIController(base.BaseController):

    def proxy_ngsi_resource(self, resource_id):
        data_dict = {'resource_id': resource_id}
        context = {'model': base.model, 'session': base.model.Session, 'user': base.c.user or base.c.author}
        return proxy_ngsi_resource(context, data_dict)
