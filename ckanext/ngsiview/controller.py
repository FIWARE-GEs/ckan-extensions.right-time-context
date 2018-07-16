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

import json
from logging import getLogger
import urlparse

import ckan.logic as logic
import ckan.lib.base as base
from ckan.plugins import toolkit
from pylons import config
import requests

log = getLogger(__name__)

CHUNK_SIZE = 512


class ProxyNGSIController(base.BaseController):

    def proxy_ngsi_resource(self, resource_id):
        # Chunked proxy for ngsi resources.
        context = {'model': base.model, 'session': base.model.Session, 'user': base.c.user or base.c.author}

        log.info('Proxify resource {id}'.format(id=resource_id))
        resource = logic.get_action('resource_show')(context, {'id': resource_id})
        verify = config.get('ckan.ngsi.verify_requests', True)

        try:

            headers = {
                'Accept': 'application/json'
            }

            if resource.get('oauth_req', 'false') == 'true':
                token = toolkit.c.usertoken['access_token']
                headers['X-Auth-Token'] = token

            if resource.get('tenant', '') != '':
                headers['FIWARE-Service'] = resource['tenant']
            if resource.get('service_path', '') != '':
                headers['FIWARE-ServicePath'] = resource['service_path']

            url = resource['url']
            parsedurl = urlparse.urlsplit(url)

            if parsedurl.scheme not in ("http", "https") or not parsedurl.netloc:
                base.abort(409, detail='Invalid URL.')

            if parsedurl.path.find('/v1/queryContext') != -1:
                if resource.get("payload", "").strip() == "":
                    details = 'Please add a payload to complete the query.'
                    base.abort(409, detail=details)

                try:
                    json.loads(resource['payload'])
                except json.JSONDecodeError:
                    details = "Payload field doesn't contain valid JSON data."
                    base.abort(409, detail=details)

                headers['Content-Type'] = "application/json"
                r = requests.post(url, headers=headers, data=resource["payload"], stream=True, verify=verify)

            else:
                r = requests.get(url, headers=headers, stream=True, verify=verify)

            if r.status_code == 401:
                if 'oauth_req' in resource and resource['oauth_req'] == 'true':
                    details = 'ERROR 401 token expired. Retrieving new token, reload please.'
                    log.info(details)
                    base.abort(409, detail=details)
                    toolkit.c.usertoken_refresh()

                elif 'oauth_req' not in resource or resource['oauth_req'] == 'false':
                    details = 'This query may need Oauth-token, please check if the token field on resource_edit is correct.'
                    log.info(details)
                    base.abort(409, detail=details)

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
