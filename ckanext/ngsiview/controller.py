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

from logging import getLogger
import urlparse
from pylons import config
import requests
import json
import ckan.logic as logic
import ckan.lib.base as base
import ckan.plugins as p

log = getLogger(__name__)

MAX_FILE_SIZE = 1024 * 1024  # 1MB
CHUNK_SIZE = 512


def proxy_ngsi_resource(context, data_dict):
    # Chunked proxy for ngsi resources.
    resource_id = data_dict['resource_id']
    log.info('Proxify resource {id}'.format(id=resource_id))
    resource = logic.get_action('resource_show')(context, {'id': resource_id})
    verify = config.get('ckan.ngsi.verify_requests', False)

    try:
        if 'oauth_req' in resource and resource['oauth_req'] == 'true':
            token = p.toolkit.c.usertoken['access_token']
            headers = {'X-Auth-Token': token, 'Content-Type': 'application/json', 'Accept': 'application/json'}
        else:
            headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}


	
        if 'tenant' in resource:
            headers['Fiware-Service'] = resource['tenant']
        if 'service_path' in resource:
            headers['Fiware-ServicePath'] = resource['service_path']


        url = resource['url']
        parts = urlparse.urlsplit(url)


	if resource['format'] == 'ngsi-h':
	    if 'tenant' not in resource or len(resource['tenant']) == 0:
                details = 'Please complete the tenant field.'
                base.abort(409, detail=details)
            if 'service_path' not in resource or len(resource['service_path']) == 0:
                details = 'Please complete the service path field.'
                base.abort(409, detail=details)

	    lastN = url.lower().find('lastn')
            hLimit = url.lower().find('hlimit')
            hOffset = url.lower().find('hoffset')

	    if lastN == -1 and (hLimit == -1 or hOffset == -1):
                details = 'if no lastN is provided hLimit and hOffset are mandatory parameters.'
                base.abort(409, detail=details)


        if not parts.scheme or not parts.netloc:
            base.abort(409, detail='Invalid URL.')

        if url.lower().find('/querycontext') != -1:
            if 'payload' in resource:
                resource['payload'] = resource['payload'].replace("'", '"')
                resource['payload'] = resource['payload'].replace(" ", "")
            else:
                details = 'Please add a  payload to complete the query.'
                base.abort(409, detail=details)

            payload = json.dumps(json.loads(resource['payload']))
            r = requests.post(url, headers=headers, data=payload, stream=True, verify=verify)

        else:
            r = requests.get(url, headers=headers, stream=True, verify=verify)

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

        else:
            r.raise_for_status()
            base.response.content_type = r.headers['content-type']
            base.response.charset = r.encoding


        length = 0
        for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
            base.response.body_file.write(chunk)
            length += len(chunk)
            if length >= MAX_FILE_SIZE:
                details = 'Content is too large to be proxied. Complete the Context Broker query with pagination parameters to resolve this issue.'
                base.abort(409, headers={'content-encoding': ''}, detail=details)

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

