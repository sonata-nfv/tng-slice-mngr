[![Build Status](https://jenkins.sonata-nfv.eu/buildStatus/icon?job=tng-slice-mngr/master)](https://jenkins.sonata-nfv.eu/job/tng-slice-mngr/master)
[![Join the chat at https://gitter.im/5gtango/tango-schema](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/5gtango/tango-schema)

<p align="center"><img src="https://github.com/sonata-nfv/tng-api-gtw/wiki/images/sonata-5gtango-logo-500px.png" /></p>

# tng-slicemgr
Description: 5GTANGO Service Platform Slice Manager

Version: 0.3

Features:
- NST, NSI management (creation, instantiation, get, termination).
- Two possible work modes:
  1) Sonata SP Emulation; it doesn't connect to any Sonata SP, instead prints the URL information to the SP. To check if the requests on the SliceManager are well done.
  2) Real Sonata SP environment; you need to install Sonata SP into the same device and configure a WIM/VIM (read "son-install" information) with and Openstack node (check RDO packstack project). 

## Required libraries
Flask, flask-restful, python-dateutil, python-uuid

## Required 5GTango components
tng-rep, tng-cat

## CONFIGURATION FILE EXAMPLE (config.cfg)

    [SLICE_MGR]
    USE_SONATA=False
    SLICE_MGR_PORT=5998

    [SONATA_COMPONENTS]
    SONATA_REP=tng-rep
    SONATA_REP_PORT=4012
    SONATA_CAT=tng-cat
    SONATA_CAT_PORT=4011

## HOW TO USE THE SLICE MANAGER:
The slice manager, has two possible work modes depending on the value given to the "USE_SONATA" parameter inside the "config.cfg" file. If the value is "True", you will work with your real SONATA SP/Openstack environement. If the value is "False", then you will work with the emulated environment (programmed inside the slice-mngr code).

Either one or the other mode is selected, you will need to open two terminal sessions (the use of "screen" might help):

1) First terminal/session: python3 main.py ./config.cfg
2) Second terminal/Session: use the commands described into the 'HOW TO "play"...' section (use the right id any time you create/delete a NST or instantiate/terminate a NSI)

## HOW TO "play"...
- STEP 1: Check the available services in Sonata SP (not working in Sonata Emulation mode)
Before working with NS Templates and Instances, user should know the available services to create NST.

   *curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X GET http://127.0.0.1:5998/api/services*

- STEP2: Manage netSlice Templates
Create/Delete and check all the NST you want/need.
	 1) CREATE NetSlice Template: To add more NetServices to compose a NetSlice Template, use this json structure in "nstNsdIds":[{"nstNsdId":"<NSuuid>"},{"nstNsdId":"<NSuuid>"}] with uuid values.

  *curl -i -H "Content-Type: application/json" -X POST -d'{"name":"NST_NAME", "version":"X.Y", "author":"AUTHOR_NAME", "vendor":"VENDOR_NAME", "nstNsdIds":[{"NsdId":"NSuuid_value"},{"nstNsdId":"NSuuid_value"}]}' http://127.0.0.1:5998/api/nst/v1/descriptors*

		    REQUEST EXAMPLE:
		    curl -i -H "Content-Type: application/json" -X POST -d'{"name":"tango_NST", "version":"1.0", "author":"5gTango", "vendor":"5gTango", "nstNsdIds":[{"NsdId":"6a01afdc-9d42-4bc9-866c-a8a3868fdf5e"}]}' http://127.0.0.1:5998/api/nst/v1/descriptors
    
		    RESPONSE EXAMPLE:
        {
          "created_at": "2018-06-08T10:36:53.425+00:00",
          "md5": "5024cfde7637ab98f086ff51bd158bc9",
          "nstd": {
            "author": "5gTango",
            "name": "tango_NST",
            "notificationTypes": "",
            "nstNsdIds": [
              "6a01afdc-9d42-4bc9-866c-a8a3868fdf5e"
            ],
            "onboardingState": "ENABLED",
            "operationalState": "ENABLED",
            "usageState": "NOT_IN_USE",
            "userDefinedData": "",
            "vendor": "5gTango",
            "version": "1.0"
          },
          "signature": null,
          "status": "active",
          "updated_at": "2018-06-08T10:36:53.425+00:00",
          "username": null,
          "uuid": "096c26f9-6142-43d2-8521-57cea9e76c6c"
        }

  2) GET AVAILABLE NSTemplates
  	
    *curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X GET http://127.0.0.1:5998/api/nst/v1/descriptors*
    
  3) GET SPECIFIC NSTemplate
  
	   *curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X GET http://127.0.0.1:5998/api/nst/v1/descriptors/{nstId}*
    
		    REQUEST EXAMPLE: 
		    curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X GET http://127.0.0.1:5998/api/nst/v1/descriptors/096c26f9-6142-43d2-8521-57cea9e76c6c

  4) DELETE NSTemplate --> it will only delete the NST when no related NSI will be used.
  
		*curl -X DELETE http://127.0.0.1:5998/api/nst/v1/descriptors/{nstId}*
	    
		    REQUEST EXAMPLE:
		    curl -X DELETE http://127.0.0.1:5998/api/nst/v1/descriptors/096c26f9-6142-43d2-8521-57cea9e76c6c

- STEP 3: Manage NetSlice Instances

Once the NST is created, it is possible to create/delete and check NSIs based on the selected NST.

  1) CREATE NetSlice Intance --> select the NST uuid by looking the nst_catalogue (NST GET actions 3 or 4) and copy the "id" you need
  
    *curl -i -H "Content-Type: application/json" -X POST -d'{"name": "NSI_NAME", "description": "NSI_DESCRIPTION", "nstId": "NST_UUID_REFERENCE"}' http://127.0.0.1:5998/api/nsilcm/v1/nsi*
    
		    REQUEST EXAMPLE:
        curl -i -H "Content-Type: application/json" -X POST -d'{"name": "5gtango_NSI", "description": "5gtango_NSI_descriptor", "nstId": "096c26f9-6142-43d2-8521-57cea9e76c6c"}' http://127.0.0.1:5998/api/nsilcm/v1/nsi

		    RESPONSE EXAMPLE:
        {
          "description": "Rubik_descriptor",
          "flavorId": "",
          "id": "deb3a1fc-2493-4d76-a65d-9ac129a213fb",
          "instantiateTime": "2018-05-11T14:16:10.773473",
          "name": "Rubik_name",
          "netServInstance_Uuid": [
            "dc8fafaf-6fab-4b4c-a6c7-a1fb5d4c2ce8"
          ],
          "nsiState": "INSTANTIATED",
          "nstId": "26c540a8-1e70-4242-beef-5e77dfa05a41",
          "nstInfoId": "",
          "sapInfo": "",
          "scaleTime": "",
          "terminateTime": "",
          "updateTime": "",
          "vendor": "5gTango"
        }
			
			NOTE: On the server side (screen managing the server), it is possible to see the emulated request sent to SONATA SP ...
			SONATA EMULATED INSTANTIATION NSI --> URL: http://10.1.7.21:32001/api/v2/requests,HEADERS: {'authorization': 'bearer None'},DATA: {"service_uuid":"40920a3c-9cc3-43f3-9f78-3fae65e29bad", "ingresses":[], "egresses":[]}

  2) GET ALL NetSlice Instances
  
		*curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X GET http://127.0.0.1:5998/api/nsilcm/v1/nsi*

  3) GET SPECIFIC NetSlice Instance
  
    *curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X GET http://127.0.0.1:5998/api/nsilcm/v1/nsi/{nsiId}*
    
		    REQUEST EXAMPLE:
        curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X GET http://127.0.0.1:5998/api/nsilcm/v1/nsi/deb3a1fc-2493-4d76-a65d-9ac129a213fb

  4) TERMINATE a NetSlice Instance
  
    This command allows you to decide when to terminate(delete) a NSI. It is possible to terminate it instantly ({"terminateTime": "0"}) or apply a future termination time {"terminateTime": "2019-04-11T10:55:30.560Z"}.
  
		*curl -i -H "Content-Type:application/json" -X POST -d '{"terminateTime": "2019-04-11T10:55:30.560Z"}' http://127.0.0.1:5998/api/nsilcm/v1/nsi/{nsiId}/terminate*
    
		    REQUEST EXAMPLES:
          1) Planned Termination: curl -i -H "Content-Type:application/json" -X POST -d '{"terminateTime": "2019-04-11T10:55:30.560Z"}' http://127.0.0.1:5998/api/nsilcm/v1/nsi/deb3a1fc-2493-4d76-a65d-9ac129a213fb/terminate
          2) Instant Termination: curl -i -H "Content-Type:application/json" -X POST -d '{"terminateTime": "0"}' http://127.0.0.1:5998/api/nsilcm/v1/nsi/deb3a1fc-2493-4d76-a65d-9ac129a213fb/terminate
        
		    NOTE: On the server side, it is possible to see the emulated request sent to SONATA SP ...
		    SONATA EMULATED TERMINATE NSI --> URL: http://10.1.7.21:32001/api/v2/requests,HEADERS: {'authorization': 'bearer None'},DATA: {"service_instance_uuid":"59cf2b1f-2a4d-4ab7-b160-9ed88d3b9dc2", "request_type":"TERMINATE"}

## License

This 5GTANGO component is published under Apache 2.0 license. Please see the LICENSE file for more details.

---
## Authors contact
  * Ricard Vilalta (ricard.vilalta@cttc.es)
  * Pol Alemany (pol.alemany@cttc.cat)
