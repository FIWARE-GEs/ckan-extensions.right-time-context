How it works?
=====================

The way to create a NGSI resource is fairly simple:
1. Firstly you have to access to the resource create section and choose the option Link.

2. Fill the URL field with a Context Broker query, if your query is a convenience operation, you only have to fill the URL field with it. If instead, it is a standard operation query, you have to do an additional step after create the resource in order to add a payload to de query. You can control the results pagination at the same way that in a common Context Broker query.

   ![image1](/ckanext/ngsiview/instructions/img1.png?raw=true)
   ![image2](/ckanext/ngsiview/instructions/img2.png?raw=true)

3. Complete the Format field with `fiware-ngsi` and click on add resource. This is an important step, and without it the extension won’t do anything with your resource.
   ![image3](/ckanext/ngsiview/instructions/img3.png?raw=true)

4. Finally set the OAuth-token field to required if you are working with Orion ContextBroker at http://orion.lab.fiware.org:1026. Additionally you can also manage the [tenant](https://forge.fiware.org/plugins/mediawiki/wiki/fiware/index.php/Publish/Subscribe_Broker_-_Orion_Context_Broker_-_User_and_Programmers_Guide#Multi_service_tenancy) and the [service path](https://forge.fiware.org/plugins/mediawiki/wiki/fiware/index.php/Publish/Subscribe_Broker_-_Orion_Context_Broker_-_User_and_Programmers_Guide#Entity_service_paths) as the same way that it is explained at Orion Context Broker documentation.

   ![image5](/ckanext/ngsiview/instructions/img5.png?raw=true)

   If your query is a convenience type, your resource has already been created, on the contrary if it is a standard operation you have to do the next step.


5. Standard operations only: Click on manage to edit your resource, now an additional field has appeared, complete it with a payload and click on update to save your query payload.

   ![image4](/ckanext/ngsiview/instructions/img4.png?raw=true)
