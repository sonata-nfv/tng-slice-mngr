# tng-slicemgr
Description: The 5GTANGO Service Platform Slice Manager

Version: 0.2

Features:
- NST, NSI management (creation, instantiation, get, termination).
- Two modes to work with:
  1) Connection to Sonata SP; simply write the right IP@ and the users/pwd into the "config.cfg" folder inside the root folder.
  2) Sonata Sp emulation; it doesn't connect to any Sonata SP, instead prints the URL information to the SP. To check if the requests on the SliceManager are well done.


## Required libraries
Flask, flask-restful, python-dateutil, python-uuid


## HOW TO START THE SLICE MANAGER:
To configure on which mode to work, write "True" (mode 1) or "False" (mdoe 2) on the "USE_SONATA" parameter inside the "config.cfg" file. Once the mode is configured, use "screen" to open two terminal sessions:

1) First session: python main.py ./config.cfg
2) Second Session: use the following commands (use the right id any time you create/delete a NST or instantiate/terminate a NSI):


- STEP 1: Check the available services in Sonata SP

Before working with NS Templates and Instances, user should know the available services to create NST.

    curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X GET http://127.0.0.1:5998/api/services


- STEP2: Manage netSlice Templates

Create/Delete and check all the NST you want/need.

  1) CREATE NetSlice Template: To add more NetServices to compose a NetSlice Template, use this json structure in "nstNsdIds":[{"nstNsdId":"<NSuuid>"},{"nstNsdId":"<NSuuid>"}]

    curl -i -H "Content-Type:application/json" -X POST -d'{"nstName":"<NetSlice_Template_name>", "nstVersion":<version_number>, "nstDesigner":"<designer_name>", "nstNsdIds":[{"nstNsdId":"<NetService_uuid>"}]}' http://127.0.0.1:5998/api/nst/v1/descriptors

  2) GET AVAILABLE NSTemplates

    curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X GET http://127.0.0.1:5998/api/nst/v1/descriptors

  3) GET SPECIFIC NSTemplate

    curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X GET http://127.0.0.1:5998/api/nst/v1/descriptors/<nstId>

  4) DELETE NSTemplate --> it will only delete the NST when no related NSI will be used.

    curl -X DELETE http://127.0.0.1:5998/api/nst/v1/descriptors/{uuid}

- STEP 3: Manage NetSlice Instances

Once the NST is created, it is possible to create/delete and check NSIs based on the selected NST.

  1) CREATE NetSlice Intance --> select the NST uuid by looking the nst_catalogue (NST GET actions 3 or 4)

    curl -i -H "Content-Type:application/json" -X POST -d'{"nsiName": "<NetSlice_Instantiation_name>", "nsiDescription": "NetSlice_description", "nstId": "<nstID_uuid>"}' http://127.0.0.1:5998/api/nsilcm/v1/nsi

  2) GET ALL NetSlice Instances

    curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X GET http://127.0.0.1:5998/api/nsilcm/v1/nsi

  3) GET SPECIFIC NetSlice Instance

    curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X GET http://127.0.0.1:5998/api/nsilcm/v1/nsi/<nsiId>

  4) TERMINATE a NetSlice Instance

    curl -i -H "Content-Type:application/json" -X POST -d '{"terminateTime": "2019-04-11T10:55:30.560Z"}' http://127.0.0.1:5998/api/nsilcm/v1/nsi/<nsiId>/terminate