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
from threading import Thread, Lock

import objects.nsi_content as nsi
import slice2ns_mapper.mapper as mapper
import slice_lifecycle_mgr.nsi_manager2repo as nsi_repo
import slice_lifecycle_mgr.nst_manager2catalogue as nst_catalogue

mutex = Lock()

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("slicemngr:repo")
LOG.setLevel(logging.INFO)


################################## THREADs to manage services/slice requests #################################
# TO SEND SERVICE INSTANTIATIONS AND CREATE NSI
## Objctive:
## Params:
class create_nsi(Thread):
  def __init__(self, NSI, nst_json):
    Thread.__init__(self)
    self.NSI = NSI
    self.nst_json = nst_json
  def run(self):
    mutex.acquire()
    try:
      # to put in order the services within a slice in the portal
      serv_seq = 1
      for NetServ_item in self.nst_json['sliceServices']:
        data = {}
        data['name'] = self.NSI.name + "-" + NetServ_item['servname'] + "-" + str(serv_seq)
        data['service_uuid'] = NetServ_item['nsdID']
        data['callback'] = "http://tng-slice-mngr:5998/api/nsilcm/v1/nsi/"+str(self.NSI.id)+"/instantiation-change"
        #data['ingresses'] = []
        #data['egresses'] = []
        #data['blacklist'] = []
        data['sla_id'] = NetServ_item['slaID']

        # requests to instantiate NSI services to the SP
        instantiation_response = mapper.net_serv_instantiate(data)

        #serviceInstance = {}
        #serviceInstance['servId'] = instantiation_response['service']['uuid']
        #serviceInstance['servName'] = instantiation_response['service']['name']
        #serviceInstance['servInstanceId'] = "null"
        #serviceInstance['workingStatus'] = "INSTANTIATING"
        #serviceInstance['requestID'] = instantiation_response['id']

        # adds the service instance into the NSI json
        #self.NSI.netServInstance_Uuid.append(serviceInstance)
        # increaes the index for the internal slice subnets names
        serv_seq = serv_seq + 1

      # saving the NSI into the repositories
      # nsirepo_jsonresponse = nsi_repo.safe_nsi(vars(self.NSI))
    finally:
      mutex.release()

# UPDATES THE SPECIFIC SERVICE RELATED TO THE URECEIVED UPDATE INFO
## Objctive:
## Params:
class update_service_instantiation(Thread):
  def __init__(self, nsiId, request_json):
    Thread.__init__(self)
    self.nsiId = nsiId
    self.request_json = request_json
  def run(self):
    mutex.acquire()
    try:
      jsonNSI = nsi_repo.get_saved_nsi(self.nsiId)
      #TODO: improve the next 2 lines to not use this delete.
      jsonNSI["id"] = jsonNSI["uuid"]
      del jsonNSI["uuid"]

      serviceInstance = {}
      # if list is empty, full it with the first element
      if not jsonNSI['netServInstance_Uuid']:
        serviceInstance['servId'] = request_json['service_uuid']
        serviceInstance['servName'] = request_json['name']
        serviceInstance['servInstanceId'] = request_json['instance_uuid']
        serviceInstance['workingStatus'] = request_json['status']
        serviceInstance['requestID'] = request_json['id']
        # adds the service instance into the NSI json
        jsonNSI['netServInstance_Uuid'].append(serviceInstance)

      # list has at least one element
      else:
        # looks for the right service within the slice and updates it with the new data
        for service_item in jsonNSI['netServInstance_Uuid']:
          # if the current request already exists, update it.
          if (service_item['requestID'] == self.request_json['id']):
            service_item['workingStatus'] = self.request_json['status']
            if(self.request_json['instance_uuid'] != None):
              service_item['servInstanceId'] = self.request_json['instance_uuid']
            break;
        # the current request doensn't exist in the list, add it.
        else:
          serviceInstance['servId'] = request_json['service_uuid']
          serviceInstance['servName'] = request_json['name']
          serviceInstance['servInstanceId'] = request_json['instance_uuid']
          serviceInstance['workingStatus'] = request_json['status']
          serviceInstance['requestID'] = request_json['id']
          # adds the service instance into the NSI json
          jsonNSI['netServInstance_Uuid'].append(serviceInstance)

      jsonNSI['updateTime'] = str(datetime.datetime.now().isoformat())
      repo_responseStatus = nsi_repo.update_nsi(jsonNSI, self.nsiId)

    finally:
      mutex.release()

# TO NOTIFY UPDATES OF A SLICE
## Objctive: used to inform about both slice instantiation or termination processes
## Params:
class notify_slice(Thread):
  def __init__(self, nsiId):
    Thread.__init__(self)
    self.nsiId = nsiId
  def run(self):
    mutex.acquire()
    try:
      jsonNSI = nsi_repo.get_saved_nsi(self.nsiId)

      LOG.info("NSI_MNGR: Checking if the slice has all services ready/error or instantiating")
      time.sleep(0.1)
      # checks if all services are READY/ERROR to update the slice_status
      all_services_ready = True
      for service_item in jsonNSI['netServInstance_Uuid']:
        LOG.info("NSI_MNGR: Checking service status: "+ str(service_item['workingStatus']))
        time.sleep(0.1)
        if (service_item['workingStatus'] == "INSTANTIATING"):
          all_services_ready = False
          break;

      LOG.info("NSI_MNGR: allServiceDone_value: "+ str(all_services_ready))
      time.sleep(0.1)
      if (all_services_ready == True):
        LOG.info("NSI_MNGR: All services instantiated, updating slice information.")
        time.sleep(0.1)
        jsonNSI['nsiState'] = "INSTANTIATED"

        # validates if any service has error status to apply it to the slice status
        for service_item in jsonNSI['netServInstance_Uuid']:
          if (service_item['workingStatus'] == "ERROR"):
            jsonNSI['nsiState'] = "ERROR"
            break;

        # updates NetSlice template list of slice_instances based on that template
        if(jsonNSI['nsiState'] == "INSTANTIATED"):
          updateNST_jsonresponse = addNSIinNST(jsonNSI["nstId"], self.nsiId)

        # sends the updated NetSlice instance to the repositories
        LOG.info("NSI_MNGR: Updating repositories with the updated NSI.")
        time.sleep(0.1)
        jsonNSI['updateTime'] = str(datetime.datetime.now().isoformat())

        repo_responseStatus = nsi_repo.update_nsi(jsonNSI, self.nsiId)

    finally:
      mutex.release()
      #INFO: leave here & don't join with the same previous IF, as the multiple return(s) depend on this order
      if (all_services_ready == True):
        LOG.info("NSI_MNGR: Notifying the GK that a slice instantiation process FINISHED")
        time.sleep(0.1)
        # creates a thread with the callback URL to advise the GK this slice is READY
        slice_callback = jsonNSI['sliceCallback']
        json_slice_info = {}
        json_slice_info['status'] = jsonNSI['nsiState']
        json_slice_info['updateTime'] = jsonNSI['updateTime']

        thread_response = mapper.sliceUpdated(slice_callback, json_slice_info)
        time.sleep(0.1)
        LOG.info("NSI_MNGR_Thread: GTK informed & NSI process finished:" + str(thread_response))

################################ NSI CREATION & INSTANTIATION SECTION ##################################
# Does all the process to create the NSI object (gathering the information and sending orders to GK)
def createNSI(nsi_json):
  LOG.info("NSI_MNGR: Creates a new NSI: " + str(nsi_json))
  time.sleep(0.1)
  nstId = nsi_json['nstId']
  catalogue_response = nst_catalogue.get_saved_nst(nstId)
  nst_json = catalogue_response['nstd']

  # creates NSI with the received information
  NSI = parseNewNSI(nst_json, nsi_json)

  # saving the NSI into the repositories
  nsirepo_jsonresponse = nsi_repo.safe_nsi(vars(self.NSI))

  #thread_create = create_nsi(NSI, nst_json)
  #thread_create.start()
  serv_seq = 1
  for NetServ_item in self.nst_json['sliceServices']:
    data = {}
    data['name'] = self.NSI.name + "-" + NetServ_item['servname'] + "-" + str(serv_seq)
    data['service_uuid'] = NetServ_item['nsdID']
    data['callback'] = "http://tng-slice-mngr:5998/api/nsilcm/v1/nsi/"+str(self.NSI.id)+"/instantiation-change"
    #data['ingresses'] = []
    #data['egresses'] = []
    #data['blacklist'] = []
    data['sla_id'] = NetServ_item['slaID']

    # requests to instantiate NSI services to the SP
    instantiation_response = mapper.net_serv_instantiate(data)
    
    serv_seq = serv_seq + 1

  return vars(NSI)

# Creates the object for the previous function from the information gathered
def parseNewNSI(nst_json, nsi_json):
  LOG.info("NSI_MNGR: Parsing a new NSI from the user_info and the reference NST")
  time.sleep(0.1)
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
#TODO: make updateInstantiatingNSI & updateTerminatingNSI one single function to update any NSI
def updateInstantiatingNSI(nsiId, request_json):
  LOG.info("NSI_MNGR: get the specific NSI to update the right service information.")
  time.sleep(0.1)

  jsonNSI = nsi_repo.get_saved_nsi(nsiId)
  if (jsonNSI):

    thread_update_instance = update_service_instantiation(nsiId, request_json)
    thread_update_instance.start()

    thread_notify = notify_slice(nsiId)
    thread_notify.start()

    LOG.info("NSI_MNGR: Returning 200")
    time.sleep(0.1)
    return (jsonNSI, 200)
  else:
    LOG.info("NSI_MNGR: There is no NSIR in the db.")
    time.sleep(0.1)
    return ('{"error":"There is no NSIR in the db."}', 500)

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

  return updatedNST_jsonresponse

    
########################################## NSI TERMINATE SECTION #######################################
# Does all the process to terminate the NSI
def terminateNSI(nsiId, TerminOrder):
  LOG.info("NSI_MNGR: Terminate NSI with id: " +str(nsiId))
  time.sleep(0.1)
  mutex.acquire()
  try:
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

    # depending on the termin_time executes one action or another
    if termin_time == 0:
      NSI.terminateTime = str(datetime.datetime.now().isoformat())
      # updates the callback for the new termination request
      NSI.sliceCallback = TerminOrder['callback']

      if (NSI.nsiState == "INSTANTIATED"):
        # updates the specific service_instance information
        NSI.nsiState = "TERMINATING"
        LOG.info("NSI_MNGR_TERMINATE: Updates NSI info and sends it to repos")
        time.sleep(0.1)

        # Sends terminate requests
        for uuidNetServ_item in NSI.netServInstance_Uuid:
          LOG.info("NSI_MNGR_TERMINATE: Sending Terminate request")
          time.sleep(0.1)
          if (uuidNetServ_item['workingStatus'] != "ERROR"):
            data = {}
            data["instance_uuid"] = str(uuidNetServ_item["servInstanceId"])
            data["request_type"] = "TERMINATE_SERVICE"
            data['callback'] = "http://tng-slice-mngr:5998/api/nsilcm/v1/nsi/"+str(nsiId)+"/terminate-change"

            termination_response = mapper.net_serv_terminate(data)
            LOG.info("NSI_MNGR: TERMINATION_response: " + str(termination_response))
            time.sleep(0.1)
            
            uuidNetServ_item['workingStatus'] = "TERMINATING"
            uuidNetServ_item['requestID'] = termination_response['id']
        
        repo_responseStatus = nsi_repo.update_nsi(vars(NSI), nsiId)
        value = 200

    #TODO: manage future termination orders
    # take into account to update the internal info of the NSi with the callback coming from GTK, which will be left...
    # ... in progress until the preocedure is done.
    # verifying if the given time is a future moment respect the current time
    elif (instan_time < termin_time):
      NSI.terminateTime = str(termin_time)
      #NSI.nsiState = "TERMINATED"
      update_NSI = vars(NSI)
      repo_responseStatus = nsi_repo.update_nsi(update_NSI, nsiId)
      value = 200
    else:
      repo_responseStatus = {"error":"Wrong value: 0 for instant termination or date time later than "+NSI.instantiateTime+", to terminate in the future."}
      value = 400
  finally:
    mutex.release()
    return (repo_responseStatus, value)

# Updates a NSI being terminated with the latest informationg coming from the MANO/GK.
def updateTerminatingNSI(nsiId, request_json):
  LOG.info("NSI_MNGR_UpdateTerminate: Let's update the NSi with terminationg info.")
  time.sleep(0.1)
  mutex.acquire()
  try:
    jsonNSI = nsi_repo.get_saved_nsi(nsiId)
    #TODO: improve the next 2 lines not have to use it.
    jsonNSI["id"] = jsonNSI["uuid"]
    del jsonNSI["uuid"]

    # looks for the right service within the slice and updates it with the new data
    for service_item in jsonNSI['netServInstance_Uuid']:
      if (service_item['requestID'] == request_json['id']):
        service_item['workingStatus'] = request_json['status']
        break;

    LOG.info("NSI_MNGR_UpdateTerminate: Checking if all services are updated: " + str(jsonNSI))
    time.sleep(0.1)
    # checks if all services are READY/ERROR to update the slice_status
    allServicesDone = True
    for service_item in jsonNSI['netServInstance_Uuid']:
      if service_item['workingStatus'] == "TERMINATING":
        allServicesDone = False
        break;

    LOG.info("NSI_MNGR_UpdateTerminate: If all services are terminated/error, updates the NSI information.")
    time.sleep(0.1)
    if (allServicesDone == True):
      jsonNSI['nsiState'] = "TERMINATED"
      
      LOG.info("NSI_MNGR_UpdateTerminate: Checks if any service has status error.")
      time.sleep(0.1)
      # validates if any service has error status to apply it to the slice status
      for service_item in jsonNSI['netServInstance_Uuid']:
        if (service_item['workingStatus'] == "ERROR"):
          jsonNSI['nsiState'] = "ERROR"
          break;
      
      jsonNSI['terminateTime'] = str(datetime.datetime.now().isoformat())
      jsonNSI['updateTime'] = jsonNSI['terminateTime']
      
      if(jsonNSI['nsiState'] == "TERMINATED"):
        # updates NetSlice template list of slice_instances based on that template
        updateNST_jsonresponse = removeNSIinNST(jsonNSI['id'], jsonNSI['nstId'])

    # sends the updated NetSlice instance to the repositories
    repo_responseStatus = nsi_repo.update_nsi(jsonNSI, nsiId)
  finally:
    mutex.release()
    if (allServicesDone == True):
      LOG.info("NSI_MNGR_UpdateTerminate: Sends the thread_notification to the GK.")
      time.sleep(0.1)
      # creates a thread with the callback URL to advise the GK this slice is READY
      sliceCallback = jsonNSI['sliceCallback']
      callback_json_slice_status = {}
      callback_json_slice_status['status'] = jsonNSI['nsiState']
      callback_json_slice_status['updateTime'] = jsonNSI['updateTime']
      thread_notify = notify_slice(sliceCallback, callback_json_slice_status)
      thread_notify.start()
      
      return (repo_responseStatus, 201)  #201 - Accepted

    return (repo_responseStatus, 200)    #200 - OK

#TODO: change the point of view, when a NST has to be deleted, do not check internal list but look ...
# ... for any NSI using that NST. Like this, we avoid to change NST information in running time.
# Removes a NSI_id from the NST list of NSIs to keep track of them
def removeNSIinNST(nsiId, nstId):
  nstParameter2update = "NSI_list_ref.pop="+str(nsiId)
  updatedNST_jsonresponse = nst_catalogue.update_nst(nstParameter2update, nstId)

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