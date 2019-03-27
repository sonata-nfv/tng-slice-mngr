#!/usr/local/bin/python3.4
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
# SENDS SERVICE INSTANTIATION REQUESTS
## Objctive:
## Params:
class thread_instantiate(Thread):
  def __init__(self, NSI):
    Thread.__init__(self)
    self.NSI = NSI
  def run(self):
    # to put in order the services within a slice in the portal
    LOG.info("NSI_MNGR_Instantiate: Instantiating Services")
    time.sleep(0.1)
    for nsr_item in self.NSI['nsr-list']:
      data = {}
      data['name'] = nsr_item['nsrName']
      data['service_uuid'] = nsr_item['subnet-nsdId-ref']
      data['callback'] = "http://tng-slice-mngr:5998/api/nsilcm/v1/nsi/"+str(self.NSI['id'])+"/instantiation-change"
      #data['ingresses'] = []
      #data['egresses'] = []
      #data['blacklist'] = []
      if (nsr_item['sla-ref'] != "None"):
        data['sla_id'] = nsr_item['sla-ref']

      LOG.info("NSI_MNGR: Data of instantiation requests: " + str(data))
      time.sleep(0.1)
      # requests to instantiate NSI services to the SP
      instantiation_response = mapper.net_serv_instantiate(data)

# UPDATES THE SLICE INSTANTIATION INFORMATION
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
      LOG.info("NSI_MNGR_Update: Updating NSI instantiation")
      jsonNSI = nsi_repo.get_saved_nsi(self.nsiId)
      #TODO: improve the next 2 lines to not use this delete.
      jsonNSI["id"] = jsonNSI["uuid"]
      del jsonNSI["uuid"]

      serviceInstance = {}
      # if list is empty, full it with the first element
      # if not jsonNSI['netServInstance_Uuid']:
      #   serviceInstance['servId'] = self.request_json['service_uuid']
      #   serviceInstance['servName'] = self.request_json['name']
      #   serviceInstance['workingStatus'] = self.request_json['status']
      #   serviceInstance['requestID'] = self.request_json['id']
      #   if(self.request_json['instance_uuid'] == None):
      #     serviceInstance['servInstanceId'] = " "
      #   else:
      #     serviceInstance['servInstanceId'] = self.request_json['instance_uuid']

      #   # adds the service instance into the NSI json
      #   jsonNSI['netServInstance_Uuid'].append(serviceInstance)

      # list has at least one element
      #else:
      #  service_added = False

      # looks all the already added services and updates the right
      for service_item in jsonNSI['nsr-list']:
        # if the current request already exists, update it.
        if (service_item['nsrName'] == self.request_json['name']):
          service_item['requestId'] = self.request_json['id']
          
          if (self.request_json['status'] == "READY"):
            service_item['working-status'] = "INSTANTIATED"
          else:
            service_item['working-status'] = self.request_json['status']
          
          if (self.request_json['instance_uuid'] != None):
            service_item['nsrId'] = self.request_json['instance_uuid']                                  # used to avoid a for-else loop with the next if
          
          break;

        # # the current request doesn't exist in the list, adds it.
        # if (service_added == False):
        #   serviceInstance['servId'] = self.request_json['service_uuid']
        #   serviceInstance['servName'] = self.request_json['name']
        #   serviceInstance['workingStatus'] = self.request_json['status']
        #   serviceInstance['requestID'] = self.request_json['id']
        #   if(self.request_json['instance_uuid'] == None):
        #     serviceInstance['servInstanceId'] = " "
        #   else:
        #     serviceInstance['servInstanceId'] = self.request_json['instance_uuid']

        # # adds the service instance into the NSI json
        # jsonNSI['netServInstance_Uuid'].append(serviceInstance)

      jsonNSI['updateTime'] = str(datetime.datetime.now().isoformat())
      repo_responseStatus = nsi_repo.update_nsi(jsonNSI, self.nsiId)

    finally:
      mutex.release()

# NOTIFIES THE GTK ABOUT A SLICE INSTANTIATION
## Objctive: used to inform about both slice instantiation or termination processes
## Params:
class notify_slice_instantiated(Thread):
  def __init__(self, nsiId):
    Thread.__init__(self)
    self.nsiId = nsiId
  def run(self):
    mutex.acquire()
    try:
      LOG.info("NSI_MNGR_Notify: Slice instantitaion Notification to GTK.")
      jsonNSI = nsi_repo.get_saved_nsi(self.nsiId)
      #TODO: improve the next 2 lines to not use this delete.
      jsonNSI["id"] = jsonNSI["uuid"]
      del jsonNSI["uuid"]

      # checks if all services are READY/ERROR to update the slice_status
      all_services_ready = True
      for service_item in jsonNSI['nsr-list']:
        if (service_item['working-status'] == "INSTANTIATING"):
          all_services_ready = False
          break;

      if (all_services_ready == True):
        jsonNSI['nsi-status'] = "INSTANTIATED"

        # validates if any service has error status to apply it to the slice status
        for service_item in jsonNSI['nsr-list']:
          if (service_item['working-status'] == "ERROR"):
            jsonNSI['nsi-status'] = "ERROR"
            break;

        # sends the updated NetSlice instance to the repositories
        jsonNSI['updateTime'] = str(datetime.datetime.now().isoformat())

        repo_responseStatus = nsi_repo.update_nsi(jsonNSI, self.nsiId)

        # updates NetSlice template usageState
        if(jsonNSI['nsi-status'] == "INSTANTIATED"):
          nst_descriptor = nst_catalogue.get_saved_nst(jsonNSI['nst-ref'])
          if (nst_descriptor['nstd'].get('usageState') == "NOT_IN_USE"):
            #updateNST_jsonresponse = nstd_usagesstatus_update(jsonNSI['nst-ref'], nst_descriptor['nstd'])
            nstParameter2update = "usageState=IN_USE"
            updatedNST_jsonresponse = nst_catalogue.update_nst(nstParameter2update, jsonNSI['nst-ref'])
    
    finally:
      mutex.release()
      #INFO: leave here & don't join with the same previous IF, as the multiple return(s) depend on this order
      if (all_services_ready == True):
        # creates a thread with the callback URL to advise the GK this slice is READY
        slice_callback = jsonNSI['sliceCallback']
        json_slice_info = {}
        json_slice_info['status'] = jsonNSI['nsi-status']
        json_slice_info['updateTime'] = jsonNSI['updateTime']

        thread_response = mapper.sliceUpdated(slice_callback, json_slice_info)

# SENDS SERVICE TERMINATION REQUESTS
## Objctive:
## Params:
class thread_terminate(Thread):
  def __init__(self,nsiId):
    Thread.__init__(self)
    self.nsiId = nsiId
  def run(self):
    LOG.info("NSI_MNGR_Terminate: Terminating Services")
    jsonNSI = nsi_repo.get_saved_nsi(self.nsiId)
    for nsr_item in jsonNSI['nsr-list']:
      if (uuidNetServ_item['workingStatus'] != "ERROR"):
        data = {}
        data["instance_uuid"] = str(nsr_item["nsrId"])
        data["request_type"] = "TERMINATE_SERVICE"
        data['callback'] = "http://tng-slice-mngr:5998/api/nsilcm/v1/nsi/"+str(self.nsiId)+"/terminate-change"

        termination_response = mapper.net_serv_terminate(data)

# UPDATES THE SLICE TERMINATION INFORMATION
## Objctive:
## Params:
class update_service_termination(Thread):
  def __init__(self, nsiId, request_json):
    Thread.__init__(self)
    self.nsiId = nsiId
    self.request_json = request_json
  def run(self):
    mutex.acquire()
    try:
      LOG.info("NSI_MNGR_Update: Updating NSI Termination")
      time.sleep(0.1)
      jsonNSI = nsi_repo.get_saved_nsi(self.nsiId)
      #TODO: improve the next 2 lines to not use this delete.
      jsonNSI["id"] = jsonNSI["uuid"]
      del jsonNSI["uuid"]

      # looks for the right service within the slice and updates it with the new data
      for service_item in jsonNSI['nsr-list']:
        if (service_item['nsrId'] == self.request_json['instance_uuid']):
          service_item['requestId'] = self.request_json['id']
          if (self.request_json['status'] == "READY"):
            service_item['working-status'] = "TERMINATED"
          else:
            service_item['working-status'] = self.request_json['status']
          break;

      jsonNSI['updateTime'] = str(datetime.datetime.now().isoformat())
      repo_responseStatus = nsi_repo.update_nsi(jsonNSI, self.nsiId)
    
    finally:
      mutex.release()

# NOTIFIES THE GTK ABOUT A SLICE TERMINATION
## Objctive: used to inform about both slice instantiation or termination processes
## Params:
class notify_slice_terminated(Thread):
  def __init__(self, nsiId):
    Thread.__init__(self)
    self.nsiId = nsiId
  def run(self):
    mutex.acquire()
    try:
      LOG.info("NSI_MNGR_Notify: Slice terminationg Notification to GTK.")
      jsonNSI = nsi_repo.get_saved_nsi(self.nsiId)
      #TODO: improve the next 2 lines to not use this delete.
      jsonNSI["id"] = jsonNSI["uuid"]
      del jsonNSI["uuid"]

      # checks if all services are READY/ERROR to update the slice_status
      all_services_ready = True
      for service_item in jsonNSI['nsr-list']:
        if (service_item['working-status'] == "TERMINATING"):
          all_services_ready = False
          break;

      if (all_services_ready == True):
        jsonNSI['nsi-status'] = "TERMINATED"

        # validates if any service has error status to apply it to the slice status
        for service_item in jsonNSI['nsr-list']:
          if (service_item['workingStatus'] == "ERROR"):
            jsonNSI['nsi-status'] = "ERROR"
            break;

        # sends the updated NetSlice instance to the repositories
        jsonNSI['terminateTime'] = str(datetime.datetime.now().isoformat())
        jsonNSI['updateTime'] = jsonNSI['terminateTime']

        repo_responseStatus = nsi_repo.update_nsi(jsonNSI, self.nsiId)

        # updates NetSlice template list of slice_instances based on that template
        removeNSIinNST(jsonNSI['nst-ref'])

    finally:
      mutex.release()

      #INFO: leave here & don't join with the same previous IF, as the multiple return(s) depend on this order
      if (all_services_ready == True):
        # sends the request to notify the GTK the slice is READY
        slice_callback = jsonNSI['sliceCallback']
        json_slice_info = {}
        json_slice_info['status'] = jsonNSI['nsi-status']
        json_slice_info['updateTime'] = jsonNSI['updateTime']

        thread_response = mapper.sliceUpdated(slice_callback, json_slice_info)


################################ NSI CREATION & INSTANTIATION SECTION ##################################
# Does all the process to create the NSI object (gathering the information and sending orders to GK)
def createNSI(nsi_json):
  LOG.info("NSI_MNGR: Creates and Instantiates a new NSI.")
  time.sleep(0.1)
  nstId = nsi_json['nstId']
  catalogue_response = nst_catalogue.get_saved_nst(nstId)
  nst_json = catalogue_response['nstd']

  # creates NSI with the received information
  LOG.info("NSI_MNGR: Creating Basic NSI structure")
  time.sleep(0.1)
  new_nsir = createBasicNSI(nst_json, nsi_json)
  LOG.info("NSI_MNGR: Adding subnets infromationg into the basic structure")
  time.sleep(0.1)
  new_nsir = addSubnets2NSi(new_nsir, nst_json["slice_ns_subnets"])
  # new_nsir = addVLD2NSi(new_nsir, nst_json["slice_ns_subnets"])    #TODO: function to add VLD information into the NSI

  # saving the NSI into the repositories
  LOG.info("NSI_MNGR: Saving NSI into repositories")
  time.sleep(0.1)
  nsirepo_jsonresponse = nsi_repo.safe_nsi(new_nsir)

  # starts the thread to instantiate while sending back the response
  LOG.info("NSI_MNGR: Calling the instantiation thread.")
  time.sleep(0.1)
  thread_instantiation = thread_instantiate(new_nsir)
  thread_instantiation.start()

  return nsirepo_jsonresponse, 201

# Creates the initial NSI object to send to the repositories
def createBasicNSI(nst_json, nsi_json):
  nsir_dict = {}
  nsir_dict['id'] = str(uuid.uuid4())
  nsir_dict['name'] = nsi_json['name']
  if (nsi_json['description']):
    nsir_dict['description'] = nsi_json['description']
  else:
    nsir_dict['description'] = 'Mock_Description'
  nsir_dict['vendor'] = nst_json['vendor']
  nsir_dict['nst-ref'] = nsi_json['nstId']
  nsir_dict['nst-name'] = nst_json['name']
  nsir_dict['nst-version'] = nst_json['version']
  nsir_dict['nsi-status'] = 'INSTANTIATING'
  nsir_dict['errorLog'] = ''
  #if (nsi_json['datacenter']):
  #    nsir_dict['datacenter'] = nsi_json['datacenter']
  #else:
  nsir_dict['datacenter'] = '00000000-0000-0000-0000-000000000000'
  nsir_dict['instantiateTime'] = str(datetime.datetime.now().isoformat())
  nsir_dict['terminateTime'] = ''
  nsir_dict['scaleTime'] = ''
  nsir_dict['updateTime'] = ''
  nsir_dict['sliceCallback'] = nsi_json['callback']  #URL used to call back the GK when the slice instance is READY/ERROR
  nsir_dict['5qiValue'] = nst_json['5qi_value']
  nsir_dict['nsr-list'] = []
  nsir_dict['vldr-list'] = []

  return nsir_dict

# Adds the basic subnets information to the NSI record
def addSubnets2NSi(nsi_json, subnets_list):
  nsr_list = []
  serv_seq = 1
  for subnet_item in subnets_list:
    subnet_record = {}
    subnet_record['nsrName'] = nsi_json['name'] + "-" + subnet_item['id'] + "-" + str(serv_seq)
    subnet_record['nsrId'] = '00000000-0000-0000-0000-000000000000'
    subnet_record['subnet-ref'] = subnet_item['id']
    subnet_record['subnet-nsdId-ref'] = subnet_item['nsd-ref']
    subnet_record['sla-name'] = subnet_item['sla-name']                           #TODO: add instantiation parameters
    subnet_record['sla-ref'] = subnet_item['sla-ref']                             #TODO: add instantiation parameters
    subnet_record['working-status'] = 'INSTANTIATING'
    subnet_record['requestId'] = ''
    subnet_record['vimAccountId'] = nsi_json['datacenter']                        #TODO: add instantiation parameters
    subnet_record['isshared'] = subnet_item['is-shared']
    subnet_record['isinstantiated'] = False
    subnet_record['vld'] = []

    nsr_list.append(subnet_record)
    serv_seq = serv_seq + 1
  
  nsi_json['nsr-list'] = nsr_list
  return nsi_json

# Updates a NSI with the latest informationg coming from the MANO/GK
#TODO: make updateInstantiatingNSI & updateTerminatingNSI one single function to update any NSI
def updateInstantiatingNSI(nsiId, request_json):
  LOG.info("NSI_MNGR: Updates the NSI with the latest incoming information.")
  jsonNSI = nsi_repo.get_saved_nsi(nsiId)
  if (jsonNSI):
    LOG.info("NSI_MNGR: Calling thread to update nsi.")
    time.sleep(0.1)
    # starts the thread to update instantiation info within the services
    thread_update_instance = update_service_instantiation(nsiId, request_json)
    thread_update_instance.start()

    LOG.info("NSI_MNGR: Calling thread to notify slice ready.")
    time.sleep(0.1)
    # starts the thread to notify the GTK if the slice is ready
    thread_notify_instantiation = notify_slice_instantiated(nsiId)
    thread_notify_instantiation.start()

    return (jsonNSI, 200)
  else:
    return ('{"error":"There is no NSIR in the db."}', 500)

# Updateds the usages status of a nstd
def nstd_usagesstatus_update(nstId, nstd_item):
  #nst_json = nst_catalogue.get_saved_nst(nstId)['nstd']
  #if (nstd_item['usageState'] == "NOT_IN_USE"):
    # updates (adds) the list of NSIref of original NST
    # nstParameter2update = "NSI_list_ref.append="+str(nsiId)
    # updatedNST_jsonresponse = nst_catalogue.update_nst(nstParameter2update, nstId)

  # updates the usageState parameter
  if (nstd_item['usageState'] == "NOT_IN_USE"):
    nstParameter2update = "usageState=IN_USE"
    updatedNST_jsonresponse = nst_catalogue.update_nst(nstParameter2update, nstId)

  return updatedNST_jsonresponse

    
########################################## NSI TERMINATE SECTION #######################################
# Does all the process to terminate the NSI
def terminateNSI(nsiId, TerminOrder):
  LOG.info("NSI_MNGR: Terminates a NSI.")

  jsonNSI = nsi_repo.get_saved_nsi(nsiId)
  #TODO: improve the next 2 lines to not use this delete.
  jsonNSI["id"] = jsonNSI["uuid"]
  del jsonNSI["uuid"]

  # prepares time values to check if termination is done in the future
  if (TerminOrder['terminateTime'] == "0" or TerminOrder['terminateTime'] == 0):
    termin_time = 0
  else:
    termin_time = dateutil.parser.parse(TerminOrder['terminateTime'])
    instan_time = dateutil.parser.parse(jsonNSI['instantiateTime'])

  # depending on the termin_time executes one action or another
  if termin_time == 0 and jsonNSI['nsi-status'] == "INSTANTIATED":
    jsonNSI['terminateTime'] = str(datetime.datetime.now().isoformat())
    jsonNSI['sliceCallback'] = TerminOrder['callback']
    jsonNSI['nsi-status'] = "TERMINATING"

    for terminate_nsr_item in jsonNSI['nsr-list']:
      if (terminate_nsr_item['working-status'] != "ERROR"):
        terminate_nsr_item['working-status'] = "TERMINATING"

    LOG.info("NSI_MNGR: Updating initial nsi with this dict:" + str(jsonNSI))
    repo_responseStatus = nsi_repo.update_nsi(jsonNSI, nsiId)

    # starts the thread to terminate while sending back the response
    thread_termination = thread_terminate(nsiId)
    thread_termination.start()
    
    value = 200

  # TODO: manage future termination orders
  elif (instan_time < termin_time):
    jsonNSI['terminateTime'] = str(termin_time)
    repo_responseStatus = nsi_repo.update_nsi(jsonNSI, nsiId)
    value = 200
  else:
    repo_responseStatus = {"error":"Wrong value: 0 for instant termination or date time later than "+NSI.instantiateTime+", to terminate in the future."}
    value = 400

  return (repo_responseStatus, value)

# Updates a NSI being terminated with the latest informationg coming from the MANO/GK.
def updateTerminatingNSI(nsiId, request_json):
  LOG.info("NSI_MNGR: get the specific NSI to update the right service information.")
  jsonNSI = nsi_repo.get_saved_nsi(nsiId)
  if (jsonNSI):
    # starts the thread to update termination info within the services
    thread_update_termination = update_service_termination(nsiId, request_json)
    thread_update_termination.start()

    # starts the thread to notify the GTK if the slice is ready
    thread_notify_termination = notify_slice_terminated(nsiId)
    thread_notify_termination.start()

    return (jsonNSI, 200)
  else:
    return ('{"error":"There is no NSIR in the db."}', 500)

#TODO: remove funct -> look for any INSTANTIATED nsi based on the nst: if any do nothing, else change NST usage.
# Removes a NSI_id from the NST list of NSIs to keep track of them
def removeNSIinNST(nstId):
  # ------ OLD VERSION ---------
  #nstParameter2update = "NSI_list_ref.pop="+str(nsiId)
  #updatedNST_jsonresponse = nst_catalogue.update_nst(nstParameter2update, nstId)

  # if there are no more NSI assigned to the NST, updates usageState parameter
  # catalogue_response = nst_catalogue.get_saved_nst(nstId)
  # nst_json = catalogue_response['nstd']
  # if not nst_json['NSI_list_ref']:
  #   if (nst_json['usageState'] == "IN_USE"):
  #     nstParameter2update = "usageState=NOT_IN_USE"
  #     updatedNST_jsonresponse = nst_catalogue.update_nst(nstParameter2update, nstId)
  # ----------------------------
  nsis_list = nsi_repo.getAll_saved_nsi()
  all_nsis_terminated = True
  for nsis_item in nsis_list:
    if (nsis_item['nst-ref'] == nstd_id and nsis_item['nsi-status'] == "INSTANTIATED" or nsis_item['nsi-status'] == "INSTANTIATING" or nsis_item['nsi-status'] == "READY"):
        all_nsis_terminated = False
        break;

  if (all_nsis_terminated):
    nst_descriptor = nst_catalogue.get_saved_nst(nstId)
    nst_json = nst_descriptor['nstd']
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