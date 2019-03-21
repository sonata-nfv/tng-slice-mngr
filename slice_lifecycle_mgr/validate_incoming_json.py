"""
## Copyright (c) 2015 SONATA-NFV, 2017 5GTANGO [, ANY ADDITIONAL AFFILIATION]
## ALL RIGHTS RESERVED.
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
##
## Neither the name of the SONATA-NFV, 5GTANGO [, ANY ADDITIONAL AFFILIATION]
## nor the names of its contributors may be used to endorse or promote
## products derived from this software without specific prior written
## permission.
##
## This work has been performed in the framework of the SONATA project,
## funded by the European Commission under Grant number 671517 through
## the Horizon 2020 and 5G-PPP programmes. The authors would like to
## acknowledge the contributions of their colleagues of the SONATA
## partner consortium (www.sonata-nfv.eu).
##
## This work has been performed in the framework of the 5GTANGO project,
## funded by the European Commission under Grant number 761493 through
## the Horizon 2020 and 5G-PPP programmes. The authors would like to
## acknowledge the contributions of their colleagues of the 5GTANGO
## partner consortium (www.5gtango.eu).
"""
#!/usr/bin/python

import json, datetime
from uuid import UUID

# Global variables
returnData = {}

# Validation Functions
def is_valid_uuid(uuid_to_test, version=4):
    """ Check if uuid_to_test is a valid UUID.
    Parameters -> uuid_to_test : str / version : {1, 2, 3, 4}
    Returns ----> `True` if a valid UUID, otherwise `False`.
    """
    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except:
        return False
    #return str(uuid_obj) == uuid_to_test
    return uuid_obj


# CASE: Create NetSlice Template
#Json_example:
# {
#   "name":"tango_NST",
#   "version":"1.0",
#   "author":"5gtango",
#   "vendor":"5gTango",
#   "nstNsdIds":[
#     {"servname":"ser_1","nsdID": "c3305e70-4e6a-4741-91d2-672f00cdd437","slaID": "75ecf965-1afd-4330-b883-8672c2563785"},
#   ]
# }
def validateCreateTemplate (jsonData):
  for item in jsonData['sliceServices']:
    LOG.info('FormValidator check slaID: ' + str(item['slaID']))
    if (is_valid_uuid (item['slaID']) == True):
      returnData["missing_field"] = "UUID value is OK!!"
      return (returnData, 201)
    elif item['slaID'] == None:
      returnData["missing_field"] = "None value is OK!!"
      return (returnData, 201)
    else:
      returnData["missing_field"] = "The Service Level Agreement (SLA) ID format is wrong, please check it."
      return (returnData, 400)

# CASE: Create NetSlice instantiation
# Json_example: {"name": "NSI_name", "description": "NSI_descriptor", "nstId": "26c540a8-1e70-4242-beef-5e77dfa05a41"}
def validateCreateInstantiation (jsonData):
  if (is_valid_uuid(jsonData['nstId']) == True):
    returnData["missing_field"] = "Everything is OK!!"
    return (returnData, 200)
  else:
    returnData["missing_field"] = "The Network Service Template ID format is wrong, please check it."
    LOG.info('FormValidator NSI_Error: ' + str(returnData))
    return (returnData, 400)

# CASE: Terminate NetSlice Instantiation
# Json_example: jsonData = {"terminateTime": <time>}
# Possible values for <time> --> instant_termination: 0 / future termination: 2019-07-16T14:01:31.447547
def validateTerminateInstantiation (jsonData):
  if (jsonData['terminateTime'] == 0 or jsonData['terminateTime'] == "0"):
    returnData["missing_field"] = "Everything is OK!!"
    return (returnData, 200)
  else:
    try:
      datetime.datetime.strptime(jsonData['terminateTime'],'%Y-%m-%dT%H:%M:%S.%f')
      returnData["missing_field"] = "Everything is OK!!"
      return (returnData, 200)
    except ValueError:
      returnData["missing_field"] = "Incorrect data format, give value 0 (instant termination) or follow this structure YYYY-MM-DDTHH:MM:SS.ffff"
      LOG.info('FormValidator Termination_Error: ' + str(returnData))
      return (returnData, 400)
