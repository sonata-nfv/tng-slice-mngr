# tng-slicemgr
Description: 5GTANGO Service Platform Slice Manager

Version: 0.3

Features:
- NST, NSI management (creation, instantiation, get, termination).
- Two possible work modes:
  1) Connection to Sonata SP; simply write the right IP@ and the users/pwd into the "config.cfg" file inside the root folder.
  2) Sonata SP Emulation; it doesn't connect to any Sonata SP, instead prints the URL information to the SP. To check if the requests on the SliceManager are well done.

## Required libraries
Flask, flask-restful, python-dateutil, python-uuid

## CONFIGURATION FILE EXAMPLE (config.cfg)

    [SLICE_MGR]
    USE_SONATA=False
    SONATA_SP_IP=10.1.7.21    
    SONATA_SP_USER=sonata
    SONATA_SP_PWD=1234

## HOW TO START THE SLICE MANAGER:
To configure on which mode to work, write "True" (mode 1) or "False" (mode 2) on the "USE_SONATA" parameter inside the "config.cfg" file. Once the mode is configured, use "screen" to open two terminal sessions:

1) First session: python main.py ./config.cfg (it also works with python3)
2) Second Session: use the following commands (use the right id any time you create/delete a NST or instantiate/terminate a NSI):

## HOW TO "play"...
- STEP 1: Check the available services in Sonata SP
Before working with NS Templates and Instances, user should know the available services to create NST.

   *curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X GET http://127.0.0.1:5998/api/services*

- STEP2: Manage netSlice Templates
Create/Delete and check all the NST you want/need.
	 1) CREATE NetSlice Template: To add more NetServices to compose a NetSlice Template, use this json structure in "nstNsdIds":[{"nstNsdId":"<NSuuid>"},{"nstNsdId":"<NSuuid>"}]

	*curl -i -H "Content-Type:application/json" -X POST -d'{"nstName":"<NetSlice_Template_name>", "nstVersion":<version_number>, "nstDesigner":"<designer_name>", "nstNsdIds":[{"nstNsdId":"<NetService_uuid>"}]}' http://127.0.0.1:5998/api/nst/v1/descriptors*

		    REQUEST EXAMPLE:
		    ccurl -i -H "Content-Type:application/json" -X POST -d'{"nstName":"Rubik_NST", "nstVersion":1, "nstDesigner":"Rubik_designer", "nstNsdIds":[{"nstNsdId":"40920a3c-9cc3-43f3-9f78-3fae65e29bad"}]}' http://127.0.0.1:5998/api/nst/v1/descriptors
    
		    RESPONSE EXAMPLE:
		     {
			      "notificationTypes": "",
			      "nstDesigner": "Rubik_designer",
			      "nstId": "185c00c8-fe09-4fc5-9175-ebbcd757e0f5",
			      "nstInvariantId": "",
			      "nstName": "Rubik_NST",
			      "nstNsdIds": [
			          "40920a3c-9cc3-43f3-9f78-3fae65e29bad"
			      ],
			      "nstOnboardingState": "ENABLED",
			      "nstOperationalState": "ENABLED",
			      "nstUsageState": "NOT_USED",
			      "nstVersion": 3,
			      "userDefinedData": ""
		      }

  2) GET AVAILABLE NSTemplates
  	
    *curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X GET http://127.0.0.1:5998/api/nst/v1/descriptors*
    
  3) GET SPECIFIC NSTemplate
  
	   *curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X GET http://127.0.0.1:5998/api/nst/v1/descriptors/{nstId}*
    
		    REQUEST EXAMPLE: 
		    curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X GET http://127.0.0.1:5998/api/nst/v1/descriptors/185c00c8-fe09-4fc5-9175-ebbcd757e0f5

  4) DELETE NSTemplate --> it will only delete the NST when no related NSI will be used.
  
		*curl -X DELETE http://127.0.0.1:5998/api/nst/v1/descriptors/{nstId}*
	    
		    REQUEST EXAMPLE:
		    curl -X DELETE http://127.0.0.1:5998/api/nst/v1/descriptors/185c00c8-fe09-4fc5-9175-ebbcd757e0f5

- STEP 3: Manage NetSlice Instances

Once the NST is created, it is possible to create/delete and check NSIs based on the selected NST.

  1) CREATE NetSlice Intance --> select the NST uuid by looking the nst_catalogue (NST GET actions 3 or 4)
  
	  *curl -i -H "Content-Type:application/json" -X POST -d'{"nsiName": "<NetSlice_Instantiation_name>", "nsiDescription": "NetSlice_description", "nstId": "<nstID_uuid>"}' http://127.0.0.1:5998/api/nsilcm/v1/nsi*
    
		    REQUEST EXAMPLE: curl -i -H "Content-Type:application/json" -X POST -d'{"nsiName": "<Rubik_NSI>", "nsiDescription": "Rubik_NSI_description", "nstId": "185c00c8-fe09-4fc5-9175-ebbcd757e0f5"}' http://127.0.0.1:5998/api/nsilcm/v1/nsi
		    RESPONSE EXAMPLE:
		    {
				    "ServiceInstancesUuid": [
						    "59cf2b1f-2a4d-4ab7-b160-9ed88d3b9dc2"
					],
					"flavorId": "",
					"instantiateTime": "2018-04-11T15:48:34.736264",
					"nsiDescription": "Rubik_NSI_description",
					"nsiId": "77fabee0-1b40-4327-b298-7fc3167c66c2",
					"nsiName": "<Rubik_NSI>",
					"nsiState": "INSTANTIATED",
					"nstId": "185c00c8-fe09-4fc5-9175-ebbcd757e0f5",
					"nstInfoId": "",
					"sapInfo": "",
					"scaleTime": "",
					"terminateTime": "",
					"updateTime": ""
			}
			
			NOTE: On the server side, it is possible to see the emulated request sent to SONATA SP ...
			SONATA EMULATED TOKEN REQUEST --> URL: http://10.1.7.21:32001/api/v2/sessions,DATA: {"username":"sonata","password":"1234"}
			SONATA EMULATED INSTANTIATION NSI --> URL: http://10.1.7.21:32001/api/v2/requests,HEADERS: {'authorization': 'bearer None'},DATA: {"service_uuid":"40920a3c-9cc3-43f3-9f78-3fae65e29bad", "ingresses":[], "egresses":[]}

  2) GET ALL NetSlice Instances
  
		*curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X GET http://127.0.0.1:5998/api/nsilcm/v1/nsi*

  3) GET SPECIFIC NetSlice Instance
  
	    *curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X GET http://127.0.0.1:5998/api/nsilcm/v1/nsi/{nsiId}*
    
		    REQUEST EXAMPLE: curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X GET http://127.0.0.1:5998/api/nsilcm/v1/nsi/77fabee0-1b40-4327-b298-7fc3167c66c2

  4) TERMINATE a NetSlice Instance
  
		*curl -i -H "Content-Type:application/json" -X POST -d '{"terminateTime": "2019-04-11T10:55:30.560Z"}' http://127.0.0.1:5998/api/nsilcm/v1/nsi/{nsiId}/terminate*
    
		    REQUEST EXAMPLE: curl -i -H "Content-Type:application/json" -X POST -d '{"terminateTime": "2019-04-11T10:55:30.560Z"}' http://127.0.0.1:5998/api/nsilcm/v1/nsi/77fabee0-1b40-4327-b298-7fc3167c66c2/terminate

		    NOTE: On the server side, it is possible to see the emulated request sent to SONATA SP ...
		    SONATA EMULATED TOKEN REQUEST --> URL: http://10.1.7.21:32001/api/v2/sessions,DATA: {"username":"sonata","password":"1234"}
		    SONATA EMULATED TERMINATE NSI --> URL: http://10.1.7.21:32001/api/v2/requests,HEADERS: {'authorization': 'bearer None'},DATA: {"service_instance_uuid":"59cf2b1f-2a4d-4ab7-b160-9ed88d3b9dc2", "request_type":"TERMINATE"}


## Authors contact
  * Ricard Vilalta (ricard.vilalta@cttc.es)
  * Pol Alemany (pol.alemany@cttc.cat)
