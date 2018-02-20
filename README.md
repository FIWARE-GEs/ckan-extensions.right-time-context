CKAN ckanext-ngsiview
=====================

[![Build Status](https://travis-ci.org/conwetlab/ckanext-ngsiview.svg?branch=ngsiv2)](https://travis-ci.org/conwetlab/ckanext-ngsiview)
[![Coverage Status](https://coveralls.io/repos/github/conwetlab/ckanext-ngsiview/badge.svg?branch=ngsiv2)](https://coveralls.io/github/conwetlab/ckanext-ngsiview?branch=ngsiv2)

CKAN extension that will give you the ability to manage real-time resources provided by a FIWARE Context Broker. This extension also provides a basic view to provide a data preview to user browsing context broker resources, altough it can be combined with other plugins (e.g. the [`ckanext-wirecloud_view`](https://github.com/conwetlab/ckanext-wirecloud_view.git) one) to provide a more advanced visualization of the data provided using CKAN.

**Note**: This extension is being tested in CKAN 2.5, 2.6 and 2.7. These are
therefore considered as the supported versions


## Requirements

* [OAuth2 CKAN Extension](https://github.com/conwetlab/ckanext-oauth2/). This extension is required to make request to secured Context Broker instances. The autentication token will be taken from the current user session, so the accessed context broker must be connected to the same IdM server as the one used to login into CKAN, if not, the token will not work.


## Installation

To install ckanext-ngsiview:

1. Activate your CKAN virtual environment, for example:

    ```
    . /usr/lib/ckan/default/bin/activate
    ```

2. Install the ckanext-ngsiview Python package into your virtual environment:

    ```
    pip install ckanext-ngsiview
    ```

3. Add `ngsiview` to the `ckan.plugins` setting in your CKAN
   config file (e.g. `/etc/ckan/default/production.ini`).

4. Restart CKAN. For example if you've deployed CKAN with Apache:

    ```
    sudo service apache2 graceful
    ```


## Development Installation

To install `ckanext-ngsiview` for development, activate your CKAN virtualenv and
do:

```
git clone https://github.com/conwetlab/ckanext-ngsiview.git
cd ckanext-ngsiview
python setup.py develop
```


## How it works

The way to create a NGSI resource is fairly simple:

1. Firstly you have to access to the form for creating a new resource.

3. Complete the Format field with `fiware-ngsi` and click on add resource. This is an important step, and without it the extension won’t do anything with your resource.
   ![image3](/ckanext/ngsiview/instructions/img3.png?raw=true)
2. Fill the URL field with a Context Broker query, if your query is a convenience operation, you only have to fill the URL field with it.

   ![image1](/ckanext/ngsiview/instructions/img1.png?raw=true)
   ![image2](/ckanext/ngsiview/instructions/img2.png?raw=true)


4. Finally set the OAuth-token field to required if you are working with Context Broker at . Additionally you can also manage the [tenant](https://forge.fiware.org/plugins/mediawiki/wiki/fiware/index.php/Publish/Subscribe_Broker_-_Orion_Context_Broker_-_User_and_Programmers_Guide#Multi_service_tenancy) and the [service path](https://forge.fiware.org/plugins/mediawiki/wiki/fiware/index.php/Publish/Subscribe_Broker_-_Orion_Context_Broker_-_User_and_Programmers_Guide#Entity_service_paths) as the same way that it is explained at Orion Context Broker documentation.

   ![image5](/ckanext/ngsiview/instructions/img5.png?raw=true)
