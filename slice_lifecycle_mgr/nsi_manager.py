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

import os, sys, logging, datetime, uuid, time, json
import dateutil.parser
from threading import Thread

import objects.nsi_content as nsi
import slice2ns_mapper.mapper as mapper
import slice_lifecycle_mgr.nsi_manager2repo as nsi_repo
import slice_lifecycle_mgr.nst_manager2catalogue as nst_catalogue

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("slicemngr:repo")
LOG.setLevel(logging.INFO)


################################## THREAD TO NOTIFY UPDATES IN A SLICE #################################
## Objctive: used to inform about both slice instantiation or termination processes
## Params:
##  callback_endpoint --> the URL to call the Gatekeeper
##  nsi_json -----------> json with the last version of the NSI created sent to the Gatekeeper.
class Notify_Slice(Thread):
  def __init__(self, callback_endpoint, nsi_status_json):
    Thread.__init__(self)
    self.callback_endpoint = callback_endpoint
    self.status = nsi_status_json
  def run(self):
    thread_response = mapper.sliceUpdated(self.callback_endpoint, self.status)
    time.sleep(0.1)
    LOG.info("NSI_MNGR_Thread: GTK informed & NSI process finished:" + str(thread_response))



################################ NSI CREATION & INSTANTIATION SECTION ##################################
# Does all the process to create the NSI object (gathering the information and sending orders to GK)
def createNSI(nsi_json):
  LOG.info("NSI_MNGR: Creating a new NSI: " + str(nsi_json))
  nstId = nsi_json['nstId']
  catalogue_response = nst_catalogue.get_saved_nst(nstId)
  nst_json = catalogue_response['nstd']
  LOG.info("NSI_MNGR: Getting NST: " + str(nst_json))

  LOG.info("NSI_MNGR: parsing the NSI object")
  # creates NSI with the received information
  NSI = parseNewNSI(nst_json, nsi_json)

  LOG.info("NSI_MNGR: Sending request to instantiate services within the NST")
  # to put in order the services within a slice in the protal
  serv_seq = 1
  for NetServ_item in nst_json['sliceServices']:
    data = {}
    data['name'] = NSI.name + "-" + NetServ_item['servname'] + "-" + str(serv_seq)
    data['service_uuid'] = NetServ_item['nsdID']
    data['callback'] = "http://tng-slice-mngr:5998/api/nsilcm/v1/nsi/"+str(NSI.id)+"/instantiation-change"
    #data['ingresses'] = []
    #data['egresses'] = []
    #data['blacklist'] = []
    data['sla_id'] = NetServ_item['slaID']
    
    # requests to instantiate NSI services to the SP
    instantiation_response = mapper.net_serv_instantiate(data)
    LOG.info("NSI_MNGR: INSTANTIATION_response: " + str(instantiation_response))
    
    serviceInstance = {}
    serviceInstance['servId'] = instantiation_response['service']['uuid']
    serviceInstance['servName'] = instantiation_response['service']['name']
    serviceInstance['servInstanceId'] = "null"
    serviceInstance['workingStatus'] = "INSTANTIATING"
    serviceInstance['requestID'] = instantiation_response['id']
    # adds the service instance into the NSI json
    NSI.netServInstance_Uuid.append(serviceInstance)

    serv_seq = serv_seq + 1

  LOG.info("NSI_MNGR: saving the slice instance information")
  # saving the NSI into the repositories
  NSI_string = vars(NSI)
  nsirepo_jsonresponse = nsi_repo.safe_nsi(NSI_string)

  return nsirepo_jsonresponse

# Creates the object for the previous function from the information gathered
def parseNewNSI(nst_json, nsi_json):
  LOG.info("NSI_MNGR: Parsing a new NSI from the user_info and the reference NST")
  uuid_nsi = str(uuid.uuid4())
  if nsi_json['name']:
    name = nsi_json['name']
  else:
    name = "Mock_Name"

  if nsi_json['description']:
    description = nsi_json['description']
  else:
    description = "Mock_Description"

  nstId = nsi_json['nstId']
  vendor = nst_json['vendor']
  nstName = nst_json['name']
  nstVersion = nst_json['version']
  flavorId = ""                                           #TODO: where does it come from??
  sapInfo = ""                                            #TODO: where does it come from??
  nsiState = "INSTANTIATING"
  instantiateTime = str(datetime.datetime.now().isoformat())
  terminateTime = ""
  scaleTime = ""
  updateTime = instantiateTime
  sliceCallback = nsi_json['callback']                    #URL used to call back the GK when the slice instance is READY/ERROR
  netServInstance_Uuid = []                               #values given when services are instantiated by the SP

  NSI=nsi.nsi_content(uuid_nsi, name, description, nstId, vendor, nstName, nstVersion, flavorId, 
                sapInfo, nsiState, instantiateTime, terminateTime, scaleTime, updateTime, sliceCallback, netServInstance_Uuid)
  return NSI

# Updates a NSI with the latest informationg coming from the MANO/GK
def updateInstantiatingNSI(nsiId, request_json):
  LOG.info("NSI_MNGR: get the specific NSI to update the right service information.")
  time.sleep(0.1)
  jsonNSI = nsi_repo.get_saved_nsi(nsiId)
  jsonNSI["id"] = jsonNSI["uuid"]
  del jsonNSI["uuid"]
  # looks for the right service within the slice and updates it with the new data
  for service_item in jsonNSI['netServInstance_Uuid']:
    if (service_item['requestID'] == request_json['id']):
      if(request_json['instance_uuid'] == None):
        service_item['servInstanceId'] = " "  #if it doesn'twork, use: 00000000-0000-0000-0000-000000000000
      else:
        service_item['servInstanceId'] = request_json['instance_uuid']
      service_item['workingStatus'] = request_json['status']
      break;

  LOG.info("NSI_MNGR: Checking if the slice has all services ready/error or instantiating")
  time.sleep(0.1)
  # checks if all services are READY/ERROR to update the slice_status
  allServicesDone = True
  for service_item in jsonNSI['netServInstance_Uuid']:
    LOG.info("NSI_MNGR: Checking service status: "+ str(service_item['workingStatus']))
    time.sleep(0.1)
    if (service_item['workingStatus'] == "NEW" or service_item['workingStatus'] == "INSTANTIATING"):
      allServicesDone = False
      LOG.info("NSI_MNGR: allServiceDone_value: "+ str(allServicesDone))
      time.sleep(0.1)
      break;

  if (allServicesDone == True):
    LOG.info("NSI_MNGR: All services instantiated, updating slice_status and adding its Id to the NST.")
    time.sleep(0.1)
    jsonNSI['nsiState'] = "INSTANTIATED"

    # validates if any service has error status to apply it to the slice status
    for service_item in jsonNSI['netServInstance_Uuid']:
      LOG.info("NSI_MNGR: verifying if any service is in error for the slice status.")
      time.sleep(0.1)
      if (service_item['workingStatus'] == "ERROR"):
        jsonNSI['nsiState'] = "ERROR"
        break;

    # updates NetSlice template list of slice_instances based on that template
    if(jsonNSI['nsiState'] == "INSTANTIATED"):
      LOG.info("NSI_MNGR: Adding the NSI_id into the NST register list of NSIS using it.")
      time.sleep(0.1)
      updateNST_jsonresponse = addNSIinNST(jsonNSI["nstId"], nsiId)

  # sends the updated NetSlice instance to the repositories
  LOG.info("NSI_MNGR: Updating repositorieswith the updated NSI.")
  time.sleep(0.1)
  jsonNSI['updateTime'] = str(datetime.datetime.now().isoformat())
  repo_responseStatus = nsi_repo.update_nsi(jsonNSI, nsiId)         #TODO: do we remove the nsi or leave it as record?

  #INFO: leave here & don't join with the same previous IF, as the multiple return(s) depend on this order
  if (allServicesDone == True):
    LOG.info("NSI_MNGR: Notifying the GK that a slice instantiation process FINISHED")
    time.sleep(0.1)
    # creates a thread with the callback URL to advise the GK this slice is READY
    sliceCallback = jsonNSI['sliceCallback']
    callback_json_slice_status = {}
    callback_json_slice_status['status'] = jsonNSI['nsiState']
    callback_json_slice_status['updateTime'] = jsonNSI['updateTime']
    thread_notify = Notify_Slice(sliceCallback, callback_json_slice_status)
    thread_notify.start()
    
    return (repo_responseStatus, 201)

  LOG.info("NSI_MNGR: Returning 200")
  LOG.info("NSI_MNGR: Returning repo_responseStatus: " + str(repo_responseStatus))
  time.sleep(0.1)
  return (repo_responseStatus, 200)

#TODO: change the point of view, when a NST has to be deleted, do not check internal list but look for any NSI ...
# ... using that NST. Like this, we avoid to change NST information in running time. This function will be removed.
# Adds a NSI_id into the NST list of NSIs to keep track of them
def addNSIinNST(nstId, nsiId):
  nst_json = nst_catalogue.get_saved_nst(nstId)['nstd']

  # updates the usageState parameter
  if (nst_json['usageState'] == "NOT_IN_USE"):
    nstParameter2update = "usageState=IN_USE"
    updatedNST_jsonresponse = nst_catalogue.update_nst(nstParameter2update, nstId)

  # updates (adds) the list of NSIref of original NST
  nstParameter2update = "NSI_list_ref.append="+str(nsiId)
  updatedNST_jsonresponse = nst_catalogue.update_nst(nstParameter2update, nstId)
  LOG.info('NSI_MNGR: updated NSI reference list of the NST: '+str(updatedNST_jsonresponse))
  time.sleep(0.1)

  return updatedNST_jsonresponse

    
########################################## NSI TERMINATE SECTION #######################################
# Does all the process to terminate the NSI
def terminateNSI(nsiId, TerminOrder):
  LOG.info("NSI_MNGR: Terminate NSI with id: " +str(nsiId))
  time.sleep(0.1)
  jsonNSI = nsi_repo.get_saved_nsi(nsiId)

  NSI=nsi.nsi_content(jsonNSI['uuid'], jsonNSI['name'], jsonNSI['description'], jsonNSI['nstId'], jsonNSI['vendor'],
                  jsonNSI['nstName'], jsonNSI['nstVersion'], jsonNSI['flavorId'], jsonNSI['sapInfo'], jsonNSI['nsiState'],
                  jsonNSI['instantiateTime'], jsonNSI['terminateTime'], jsonNSI['scaleTime'], jsonNSI['updateTime'],
                  jsonNSI['sliceCallback'], jsonNSI['netServInstance_Uuid'])
  LOG.info("NSI_MNGR_TERMINATE: The NSI to terminate: " +str(vars(NSI)))
  time.sleep(0.1)

  # prepares the datetime values to work with them 
  if (TerminOrder['terminateTime'] == "0" or TerminOrder['terminateTime'] == 0):
    termin_time = 0
  else:
    termin_time = dateutil.parser.parse(TerminOrder['terminateTime'])
    instan_time = dateutil.parser.parse(NSI.instantiateTime)

  LOG.info("NSI_MNGR: Looking if terminate is now or in the future.")
  time.sleep(0.1)
  # depending on the termin_time executes one action or another
  if termin_time == 0:
    LOG.info("NSI_MNGR_TERMINATE: Selected to Terminate NOW!!!")
    time.sleep(0.1)
    NSI.terminateTime = str(datetime.datetime.now().isoformat())
    # updates the callback for the new termination request
    NSI.sliceCallback = TerminOrder['callback']
    LOG.info("NSI_MNGR_TERMINATE: The NSI to terminate: " +str(vars(NSI)))
    time.sleep(0.1)

    if (NSI.nsiState == "INSTANTIATED"):
      # updates the specific service_instance information
      for uuidNetServ_item in NSI.netServInstance_Uuid:
        LOG.info("NSI_MNGR_TERMINATE: Sends terminate requests for each service")
        time.sleep(0.1)
        if (uuidNetServ_item['workingStatus'] != "ERROR"):
          data = {}
          data["instance_uuid"] = str(uuidNetServ_item["servInstanceId"])
          data["request_type"] = "TERMINATE_SERVICE"
          data['callback'] = "http://tng-slice-mngr:5998/api/nsilcm/v1/nsi/"+str(NSI.id)+"/terminate-change"
          LOG.info("CALLBACK: " +data['callback'])
          time.sleep(0.1)

          termination_response = mapper.net_serv_terminate(data)
          LOG.info("NSI_MNGR: TERMINATION_response: " + str(termination_response))
          time.sleep(0.1)
          #uuidNetServ_item['servInstanceId'] = " "
          uuidNetServ_item['workingStatus'] = "TERMINATING"
          uuidNetServ_item['requestID'] = termination_response['id']

      NSI.nsiState = "TERMINATING"

    LOG.info("NSI_MNGR_TERMINATE: Updates NSI info and sends it to repos")
    time.sleep(0.1)
    update_NSI = vars(NSI)
    repo_responseStatus = nsi_repo.update_nsi(update_NSI, nsiId)

    return (vars(NSI), 200)

  #TODO: manage future termination orders
  # take into account to update the internal info of the NSi with the callback coming from GTK, which will be left...
  # ... in progress until the preocedure is done.
  # verifying if the given time is a future moment respect the current time
  elif (instan_time < termin_time):
    NSI.terminateTime = str(termin_time)
    #NSI.nsiState = "TERMINATED"
    update_NSI = vars(NSI)
    repo_responseStatus = nsi_repo.update_nsi(update_NSI, nsiId)

    return (vars(NSI), 200)
  else:
    msg = "Wrong value: 0 for instant termination or date time later than "+NSI.instantiateTime+", to terminate in the future."
    return (msg, 400)

# Updates a NSI being terminated with the latest informationg coming from the MANO/GK.
def updateTerminatingNSI(nsiId, request_json):
  LOG.info("NSI_MNGR_UpdateTerminate: Let's update the NSi with terminationg info.")
  time.sleep(0.1)
  jsonNSI = nsi_repo.get_saved_nsi(nsiId)

  LOG.info("NSI_MNGR_UpdateTerminate: Updating the right NSI record.")
  time.sleep(0.1)
  # looks for the right service within the slice and updates it with the new data
  for service_item in jsonNSI['netServInstance_Uuid']:
    if (service_item['requestID'] == request_json['id']):
      service_item['workingStatus'] = request_json['status']
      break;

  LOG.info("NSI_MNGR_UpdateTerminate: Checking if all services are updated.")
  time.sleep(0.1)
  # checks if all services are READY/ERROR to update the slice_status
  allServicesDone = True
  for service_item in jsonNSI['netServInstance_Uuid']:
    #TODO: verify once it works if READY and NEW are used.
    #if (service_item['workingStatus'] == "READY" or service_item['workingStatus'] == "NEW" or service_item['workingStatus'] == "TERMINATING"):
    if service_item['workingStatus'] == "TERMINATING":
      allServicesDone = False
      break;

  LOG.info("NSI_MNGR_UpdateTerminate: If all services are terminated/error, updates the NSI information.")
  time.sleep(0.1)
  if (allServicesDone == True):
    jsonNSI['nsiState'] = "TERMINATED"
    
    LOG.info("NSI_MNGR_UpdateTerminate: Checks if status has to be error.")
    time.sleep(0.1)
    # validates if any service has error status to apply it to the slice status
    for service_item in jsonNSI['netServInstance_Uuid']:
      service_item['servInstanceId'] = " "
      if (service_item['workingStatus'] == "ERROR"):
        jsonNSI['nsiState'] = "ERROR"
        break;
    
    jsonNSI['terminateTime'] = str(datetime.datetime.now().isoformat())
    jsonNSI['updateTime'] = jsonNSI['terminateTime']
    
    if(jsonNSI['nsiState'] == "TERMINATED"):
      # updates NetSlice template list of slice_instances based on that template
      updateNST_jsonresponse = removeNSIinNST(jsonNSI['uuid'], jsonNSI['nstId'])

  LOG.info("NSI_MNGR_UpdateTerminate: Updated the NSI information in repositories.")
  time.sleep(0.1)
  # sends the updated NetSlice instance to the repositories
  repo_responseStatus = nsi_repo.update_nsi(jsonNSI, nsiId)

  #INFO: leave it here (do not join with the previous IF, as the multiple "return" depend on this order of the code.
  if (allServicesDone == True):
    LOG.info("NSI_MNGR_UpdateTerminate: Sends the thread_notification to the GK as slice is TERMINATED|ERROR.")
    time.sleep(0.1)
    # creates a thread with the callback URL to advise the GK this slice is READY
    sliceCallback = jsonNSI['sliceCallback']
    callback_json_slice_status = {}
    callback_json_slice_status['status'] = jsonNSI['nsiState']
    callback_json_slice_status['updateTime'] = jsonNSI['updateTime']
    thread_notify = Notify_Slice(sliceCallback, callback_json_slice_status)
    thread_notify.start()
    
    return (repo_responseStatus, 201)  #201 - Accepted

  return (repo_responseStatus, 200)    #200 - OK

#TODO: change the point of view, when a NST has to be deleted, do not check internal list but look ...
# ... for any NSI using that NST. Like this, we avoid to change NST information in running time.
# Removes a NSI_id from the NST list of NSIs to keep track of them
def removeNSIinNST(nsiId, nstId):
  nstParameter2update = "NSI_list_ref.pop="+str(nsiId)
  updatedNST_jsonresponse = nst_catalogue.update_nst(nstParameter2update, nstId)

  LOG.info("NSI_MNGR_removeNSIinNST: updates NST info: template_usagesState ")
  time.sleep(0.1)
  # if there are no more NSI assigned to the NST, updates usageState parameter
  catalogue_response = nst_catalogue.get_saved_nst(nstId)
  nst_json = catalogue_response['nstd']
  if not nst_json['NSI_list_ref']:
    if (nst_json['usageState'] == "IN_USE"):
      nstParameter2update = "usageState=NOT_IN_USE"
      updatedNST_jsonresponse = nst_catalogue.update_nst(nstParameter2update, nstId)


############################################ NSI GET SECTION ############################################
# Gets one single NSI item information
def getNSI(nsiId):
  LOG.info("NSI_MNGR: Retrieving NSI with id: " +str(nsiId))
  nsirepo_jsonresponse = nsi_repo.get_saved_nsi(nsiId)

  return nsirepo_jsonresponse

# Gets all the existing NSI items
def getAllNsi():
  LOG.info("NSI_MNGR: Retrieve all existing NSIs")
  nsirepo_jsonresponse = nsi_repo.getAll_saved_nsi()

  return nsirepo_jsonresponse