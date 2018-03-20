# tng-slicemgr
The 5GTANGO Service Platform Slice Manager

Version 0.1 --> NST and NSI defined, no relationship between them programmed yet.

## DEMO INSTRUCTIONS:

To start the slice manager, use "screen" to open two terminal sessions:

    1) First session: python main.py
    2) Second Session: use the following commands (change the id any time you create a NST or instantiate a NSI):

#NST curls

POST CREATE NST
curl -i -H "Content-Type:application/json" -X POST -d'{"id":1, "nstId":1, "nstName":"tango_NST", "nstVersion":2, "nstDesigner":"5gtango", "nstInvariantId":"1", "nstNsdIds":[{"nstNsdId":1},{"nstNsdId":2}], "nstOnboardingState":"ENABLED", "nstOperationalState":"ENABLED", "nstUsageState":"IN_USE", "notificationTypes":"Notification of tango_NST", "userDefinedData":"Data"}' http://127.0.0.1:5998/nst/v1/descriptors

GET ALL NST
curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X GET http://127.0.0.1:5998/nst/v1/descriptors

GET SPECIFIC NST
curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X GET http://127.0.0.1:5998/nst/v1/descriptors/<id>

DELETE SPECIFIC NST
curl -X DELETE http://127.0.0.1:5998/nst/v1/descriptors/<id>

-----------------------------------------------------------------------------------------------
#NSI curls

POST INSTANTIATE NSI
curl -i -H "Content-Type:application/json" -X POST -d'{"id": 1, "nsiName": "tango_NSI", "nsiDescription": "string", "nstId": 1, "nstInfoId": "string", "flavorId": "string", "sapInfo": "string", "nsiState": "NOT_INSTANTIATED", "instantiateTime": "2018-03-15T08:45:43.502"}' http://127.0.0.1:5998/nsilcm/v1/nsi

POST TERMINATE NSI
curl -i -H "Content-Type:application/json" -X POST -d'{"terminateTime":"2019-03-15T10:47:42.174"}' http://127.0.0.1:5998/nsilcm/v1/nsi/{nsiId}/terminate

GET ALL NSI
curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X GET http://127.0.0.1:5998/nsilcm/v1/nsi

GET SPECIFIC NSI
curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X GET http://127.0.0.1:5998/nsilcm/v1/nsi/{nsiId}
