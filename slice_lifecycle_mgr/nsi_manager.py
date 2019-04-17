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
import slice2ns_mapper.mapper as mapper                             # sends requests to the GTK-SP
#import slice2ns_mapper.slicer_wrapper_ia as slicer2ia               # sends requests to the IA
import slice_lifecycle_mgr.nsi_manager2repo as nsi_repo             # sends requests to the repositories
import slice_lifecycle_mgr.nst_manager2catalogue as nst_catalogue   # sends requests to the catalogues

# INFORMATION
# mutex used to ensure one single access to ddbb (repositories) for the nsi records creation/update/removal
mutex_slice2db_access = Lock()

# definition of LOG variable to make the slice logs idetified among the other possible 5GTango components.
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("slicemngr:repo")
LOG.setLevel(logging.INFO)


################################## THREADs to manage services/slice requests #################################
# SENDS NETWORK SERVICE (NS) INSTANTIATION REQUESTS
## Objctive: reads NS list in Network Slice Instance (NSI) and sends requests2GTK to instantiate them 
## Params: NSI - nsi created with the parameters given by the user and the NST saved in catalogues.
class thread_ns_instantiate(Thread):
  def __init__(self, NSI):
    Thread.__init__(self)
    self.NSI = NSI
  
  def send_instantiation_requests(self):
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

      # requests to instantiate NSI services to the SP
      instantiation_response = mapper.net_serv_instantiate(data)
  
  def send_networks_creation_request(self):
    '''
    {
      instance_id: String,        # do I generate it??
      vim_list: [
        {
          uuid: String,           # uuid of the VIM
          virtual_links: [
            {
              id: String,         # name of the network??
              access: String,     # network IP@???
              dhcp: String,       # network IP@???
              cidr: String,       # network IP@???
              qos: String,        # which kind of values and what?
              qos_requirements: {
                bandwidth_limit: { bandwidth: int, bandwidth_unit: String },
                minimum_bandwidth: { bandwidth: int, bandwidth_unit: String }
              }
            }
          ]
        }
      ]
    }
    '''
    #this function sends
    nets_creation_response = mapper.create_vim_network(network_data)

  def update_nsi_notify_instantiate(self):
    mutex_slice2db_access.acquire()
    try:
      LOG.info("NSI_MNGR_Notify: Slice instantitaion Notification to GTK.")
      time.sleep(0.1)
      jsonNSI = nsi_repo.get_saved_nsi(self.NSI['id'])
      #TODO: improve the next 2 lines to not use this delete.
      jsonNSI["id"] = jsonNSI["uuid"]
      del jsonNSI["uuid"]

      # updates the slice information befor notifying the GTK
      jsonNSI['nsi-status'] = "INSTANTIATED"
      jsonNSI['updateTime'] = str(datetime.datetime.now().isoformat())

      # validates if any service has error status to apply it to the slice status
      for service_item in jsonNSI['nsr-list']:
        if (service_item['working-status'] == "ERROR"):
          jsonNSI['nsi-status'] = "ERROR"
          break;

      # sends the updated NetSlice instance to the repositories
      repo_responseStatus = nsi_repo.update_nsi(jsonNSI, self.NSI['id'])

      # updates NetSlice template usageState
      if(jsonNSI['nsi-status'] == "INSTANTIATED"):
        nst_descriptor = nst_catalogue.get_saved_nst(jsonNSI['nst-ref'])
        if (nst_descriptor['nstd'].get('usageState') == "NOT_IN_USE"):
          nstParameter2update = "usageState=IN_USE"
          updatedNST_jsonresponse = nst_catalogue.update_nst(nstParameter2update, jsonNSI['nst-ref'])
    
    finally:
      # release the mutex for other threads
      mutex_slice2db_access.release()
      
      # creates a thread with the callback URL to advise the GK this slice is READY
      slice_callback = jsonNSI['sliceCallback']
      json_slice_info = {}
      json_slice_info['status'] = jsonNSI['nsi-status']
      json_slice_info['updateTime'] = jsonNSI['updateTime']

      thread_response = mapper.sliceUpdated(slice_callback, json_slice_info)

  def run(self):
    # TODO:Sends all the requests to create all the VLDs within the slice
    #self.send_networks_creation_request()
    # TODO:Waits until all the VLDs are created/ready or error

    # Sends all the requests to instantiate the NSs within the slice
    self.send_instantiation_requests()

    # Waits until all the NSs are instantiated/ready or error
    #deployment_timeout = 2 * 3600   # Two hours
    deployment_timeout = 1800   # 30min   #TODO: change once the GTK connection-bug is solved.
    while deployment_timeout > 0:
      LOG.info("Waiting all services are ready/instantiated or error...")
      # Check ns instantiation status
      nsi_instantiated = True
      jsonNSI = nsi_repo.get_saved_nsi(self.NSI['id'])
      for nsr_item in jsonNSI['nsr-list']: 
        if nsr_item['working-status'] not in ["INSTANTIATED", "ERROR", "READY"]:
          nsi_instantiated = False
      
      # if all services are instantiated or error, break the while loop to notify the GTK
      if nsi_instantiated:
        LOG.info("All service instantiations are ready!")
        break
   
      time.sleep(15)
      deployment_timeout -= 15
    
    LOG.info("Updating and notifying GTK")
    # Notifies the GTK that the Network Slice instantiation process is done (either complete or error)
    self.update_nsi_notify_instantiate()

# UPDATES THE SLICE INSTANTIATION INFORMATION
## Objctive: updates a the specific NS information belonging to a NSI instantiation
## Params: nsiId (uuid within the incoming request URL), request_json (incoming request payload)
class update_slice_instantiation(Thread):
  def __init__(self, nsiId, request_json):
    Thread.__init__(self)
    self.nsiId = nsiId
    self.request_json = request_json
  def run(self):
    mutex_slice2db_access.acquire()
    try:
      LOG.info("NSI_MNGR_Update: Updating NSI instantiation")
      time.sleep(0.1)
      jsonNSI = nsi_repo.get_saved_nsi(self.nsiId)
      #TODO: improve the next 2 lines to not use this delete.
      jsonNSI["id"] = jsonNSI["uuid"]
      del jsonNSI["uuid"]

      LOG.info("NSI_MNGR_Update: Checking information to update...")
      time.sleep(0.1)
      serviceInstance = {}
      # looks all the already added services and updates the right
      for service_item in jsonNSI['nsr-list']:
        # if the current request already exists, update it.
        if (service_item['nsrName'] == self.request_json['name']):
          LOG.info("NSI_MNGR_Update: Service found, let's update it")
          time.sleep(0.1)
          service_item['requestId'] = self.request_json['id']
          
          if (self.request_json['status'] == "READY"):
            service_item['working-status'] = "INSTANTIATED"
            service_item['isinstantiated'] = True
          else:
            service_item['working-status'] = self.request_json['status']
          
          LOG.info("NSI_MNGR_Update: Service updated")
          time.sleep(0.1)
          
          if (self.request_json['instance_uuid'] != None):
            service_item['nsrId'] = self.request_json['instance_uuid']                                  # used to avoid a for-else loop with the next if
          
          break;

      LOG.info("NSI_MNGR_Update: Sending NSIr updated to repositories")
      time.sleep(0.1)
      # sends updated nsi to the DDBB (tng-repositories)
      jsonNSI['updateTime'] = str(datetime.datetime.now().isoformat())
      repo_responseStatus = nsi_repo.update_nsi(jsonNSI, self.nsiId)
      LOG.info("NSI_MNGR_Update_NSI_done: " +str(jsonNSI))
      time.sleep(0.1)
    finally:
      mutex_slice2db_access.release()

# SENDS NETWORK SERVICE (NS) TERMINATION REQUESTS
## Objctive: gets the specific nsi record from db and sends the ns termination requests 2 GTK
## Params: nsiId (uuid within the incoming request URL)
class thread_ns_terminate(Thread):
  def __init__(self,nsiId):
    Thread.__init__(self)
    self.nsiId = nsiId
  
  def send_termination_requests(self):
    LOG.info("NSI_MNGR_Terminate: Terminating Services")
    time.sleep(0.1)
    jsonNSI = nsi_repo.get_saved_nsi(self.nsiId)
    for nsr_item in jsonNSI['nsr-list']:
      if (nsr_item['working-status'] != "ERROR"):
        data = {}
        data["instance_uuid"] = str(nsr_item["nsrId"])
        data["request_type"] = "TERMINATE_SERVICE"
        data['callback'] = "http://tng-slice-mngr:5998/api/nsilcm/v1/nsi/"+str(self.nsiId)+"/terminate-change"

        termination_response = mapper.net_serv_terminate(data)

  def send_networks_removal_request(self):
    '''
    {
      instance_id: String,
      vim_list: [
        {
          uuid: String,
          virtual_links: [
            {
              id: String
            }
          ]
        }
      ]
    }
    '''

  def update_nsi_notify_terminate(self):
    mutex_slice2db_access.acquire()
    try:
      LOG.info("NSI_MNGR_Notify: Slice termination Notification to GTK.")
      time.sleep(0.1)
      jsonNSI = nsi_repo.get_saved_nsi(self.nsiId)
      #TODO: improve the next 2 lines to not use this delete.
      jsonNSI["id"] = jsonNSI["uuid"]
      del jsonNSI["uuid"]

      # updateds nsir fields
      jsonNSI['nsi-status'] = "TERMINATED"

      jsonNSI['terminateTime'] = str(datetime.datetime.now().isoformat())
      jsonNSI['updateTime'] = jsonNSI['terminateTime']
      
      # validates if any service has error status to apply it to the slice status
      for service_item in jsonNSI['nsr-list']:
        if (service_item['working-status'] == "ERROR"):
          jsonNSI['nsi-status'] = "ERROR"
          break;

      # sends the updated nsi to the repositories
      repo_responseStatus = nsi_repo.update_nsi(jsonNSI, self.nsiId)

      # updates NetSlice template usageState if no other nsi is instantiated/ready
      nsis_list = nsi_repo.get_all_saved_nsi()
      all_nsis_terminated = True
      for nsis_item in nsis_list:
        if (nsis_item['nst-ref'] == nstd_id and nsis_item['nsi-status'] in ["INSTANTIATED", "INSTANTIATING", "READY"]):
            all_nsis_terminated = False
            break;
        else:
          pass
      if (all_nsis_terminated):
        nst_descriptor = nst_catalogue.get_saved_nst(nstId)
        nst_json = nst_descriptor['nstd']
        if (nst_json['usageState'] == "IN_USE"):
          nstParameter2update = "usageState=NOT_IN_USE"
          updatedNST_jsonresponse = nst_catalogue.update_nst(nstParameter2update, nstId)

    finally:
      # release the mutex for other threads
      mutex_slice2db_access.release()

      # sends the request to notify the GTK the slice is READY
      slice_callback = jsonNSI['sliceCallback']
      json_slice_info = {}
      json_slice_info['status'] = jsonNSI['nsi-status']
      json_slice_info['updateTime'] = jsonNSI['updateTime']

      thread_response = mapper.sliceUpdated(slice_callback, json_slice_info)

  def run(self):
    # Sends all the requests to instantiate the NSs within the slice
    self.send_termination_requests()

    # Waits until all the NSs are terminated/ready or error
    deployment_timeout = 2 * 3600   # Two hours
    while deployment_timeout > 0:
      LOG.info("Waiting all services are terminated or error...")
      # Check ns instantiation status
      nsi_terminated = True
      jsonNSI = nsi_repo.get_saved_nsi(self.nsiId)
      for nsr_item in jsonNSI['nsr-list']: 
        if nsr_item['working-status'] not in ["TERMINATED", "ERROR", "READY"]:
          nsi_terminated = False
      
      # if all services are instantiated or error, break the while loop to notify the GTK
      if nsi_terminated:
        LOG.info("All service termination are ready!")
        break
   
      time.sleep(10)
      deployment_timeout -= 10
    
    # Notifies the GTK that the Network Slice instantiation process is done (either complete or error)

    # TODO:Sends all the requests to create all the VLDs within the slice
    
    # TODO:Waits until all the VLDs are created/ready or error

    # Notifies the GTK that the Network Slice termination process is done (either complete or error)
    self.update_nsi_notify_terminate()

# UPDATES THE SLICE TERMINATION INFORMATION
## Objctive: updates a the specific NS information belonging to a NSI termination
## Params: nsiId (uuid within the incoming request URL), request_json (incoming request payload)
class update_slice_termination(Thread):
  def __init__(self, nsiId, request_json):
    Thread.__init__(self)
    self.nsiId = nsiId
    self.request_json = request_json
  def run(self):
    mutex_slice2db_access.acquire()
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
            service_item['isinstantiated'] = False
          else:
            service_item['working-status'] = self.request_json['status']
          break;

      jsonNSI['updateTime'] = str(datetime.datetime.now().isoformat())
      repo_responseStatus = nsi_repo.update_nsi(jsonNSI, self.nsiId)
    
    finally:
      mutex_slice2db_access.release()


################################ NSI CREATION & INSTANTIATION SECTION ##################################
# Network Slice Instance Object Creation
def create_nsi(nsi_json):
  LOG.info("NSI_MNGR: Creates and Instantiates a new NSI.")
  time.sleep(0.1)
  nstId = nsi_json['nstId']
  catalogue_response = nst_catalogue.get_saved_nst(nstId)
  nst_json = catalogue_response['nstd']

  # check if there is any other nsir with the same name, vendor, nstd_version
  nsirepo_jsonresponse = nsi_repo.get_all_saved_nsi()
  for nsir_item in nsirepo_jsonresponse:
    if (nsir_item["name"] == nsi_json['name'] and nsir_item["nst-version"] == nst_json['version'] and nsir_item["vendor"] == nst_json['vendor']):
      error_msg = '{"error":"There is already a slice with thie name/version/vendor. Change one of the values."}'
      return (error_msg, 500)

  # creates NSI with the received information
  new_nsir = add_basic_nsi_info(nst_json, nsi_json)
  
  # adds the VLD information within the NSI record
  new_nsir = add_vlds(new_nsir, nst_json["slice_vld"])
  
  # adds the NetServices (subnets) information within the NSI record
  new_nsir = add_subnets(new_nsir, nst_json["slice_ns_subnets"], nsi_json)

  # saving the NSI into the repositories
  nsirepo_jsonresponse = nsi_repo.safe_nsi(new_nsir)

  # starts the thread to instantiate while sending back the response
  thread_ns_instantiation = thread_ns_instantiate(new_nsir)
  thread_ns_instantiation.start()

  return nsirepo_jsonresponse, 201

# Basic NSI structure
def add_basic_nsi_info(nst_json, nsi_json):
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

# Sends requests to create vim networks and adds their information into the NSIr
#TODO: check what is necessary to send to the GTK ( reference json in nsi_manager.py)
def add_vlds(new_nsir, nst_vld_list):
  vldr_list = []
  for vld_item in nst_vld_list:
    vld_record = {}
    vld_record['id'] = vld_item['id']
    vld_record['name'] = vld_item['name']
    vld_record['vimAccountId'] = str(uuid.uuid4())  #TODO: comes with the request, to be improved
    vld_record['vim-net-id']  = str(uuid.uuid4())   #TODO: filled when the GTK sends back the uuid
    if 'mgmt-network' in vld_item.keys():
      vld_record['mgmt-network'] = True
    vld_record['type'] = vld_item['type']
    #vld_record['root-bandwidth']
    #vld_record['leaf-bandwidth']                   #TODO: check how to use this 4 parameters
    #vld_record['physical-network']
    #vld_record['segmentation_id']
    vld_record['vld-status'] = 'INACTIVE'
    vld_record['shared-nsrs-list'] = []   # this is filled when a shared service is instantiated on this VLD
    vld_record['ns-conn-point-ref'] = []  # this is filled when a service is instantiated on this VLD   
    vld_record['requestId'] = str(uuid.uuid4())    #TODO: filled when the GTK sends back the uuid

    vldr_list.append(vld_record)
  
  new_nsir['vldr-list'] = vldr_list
  return new_nsir

# Adds the basic subnets information to the NSI record
def add_subnets(new_nsir, subnets_list, request_nsi_json):
  nsr_list = []                         # empty list to add all the created slice-subnets
  serv_seq = 1                          # to put in order the services within a slice in the portal
  
  for subnet_item in subnets_list:
    subnet_record = {}
    subnet_record['nsrName'] = new_nsir['name'] + "-" + subnet_item['id'] + "-" + str(serv_seq)
    subnet_record['nsrId'] = '00000000-0000-0000-0000-000000000000'
    subnet_record['subnet-ref'] = subnet_item['id']
    subnet_record['subnet-nsdId-ref'] = subnet_item['nsd-ref']
    
    if 'services_sla' in  request_nsi_json:
      for serv_sla_item in services_sla:
        if serv_sla_item['service_uuid'] == subnet_item['nsd-ref']:
          subnet_record['sla-name'] = serv_sla_item['sla_name']                           #TODO: add instantiation parameters
          subnet_record['sla-ref'] = serv_sla_item['sla_uuid']                            #TODO: add instantiation parameters
    else:
      subnet_record['sla-name'] = "None"
      subnet_record['sla-ref'] = "None"
    
    subnet_record['working-status'] = 'INSTANTIATING'
    subnet_record['requestId'] = ''
    subnet_record['vimAccountId'] = new_nsir['datacenter']                        #TODO: add instantiation parameters
    subnet_record['isshared'] = subnet_item['is-shared']
    subnet_record['isinstantiated'] = False
    subnet_record['vld'] = []

    nsr_list.append(subnet_record)
    serv_seq = serv_seq + 1
  
  new_nsir['nsr-list'] = nsr_list
  return new_nsir

# Updates a NSI with the latest information coming from the MANO/GK
def update_instantiating_nsi(nsiId, request_json):
  LOG.info("NSI_MNGR: Updates the NSI with the latest incoming information.")
  time.sleep(0.1)
  jsonNSI = nsi_repo.get_saved_nsi(nsiId)
  if (jsonNSI):
    # starts the thread to update instantiation info within the services
    thread_update_slice_instantiation = update_slice_instantiation(nsiId, request_json)
    time.sleep(0.1)
    thread_update_slice_instantiation.start()

    # starts the thread to notify the GTK if the slice is ready
    #thread_notify_slice_instantiatied = notify_slice_instantiated(nsiId)
    #time.sleep(0.1)
    #thread_notify_slice_instantiatied.start()

    return (jsonNSI, 200)
  else:
    return ('{"error":"There is no NSIR in the db."}', 500)

    
########################################## NSI TERMINATE SECTION #######################################
# Does all the process to terminate the NSI
def terminate_nsi(nsiId, TerminOrder):
  LOG.info("NSI_MNGR: Terminates a NSI.")
  time.sleep(0.1)

  jsonNSI = nsi_repo.get_saved_nsi(nsiId)
  if (jsonNSI):
    #TODO: improve the next 2 lines to not use this delete.
    jsonNSI["id"] = jsonNSI["uuid"]
    del jsonNSI["uuid"]

    # prepares time values to check if termination is done in the future
    if (TerminOrder['terminateTime']) == "0" or TerminOrder['terminateTime'] == 0):
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

      repo_responseStatus = nsi_repo.update_nsi(jsonNSI, nsiId)

      # starts the thread to terminate while sending back the response
      thread_ns_termination = thread_ns_terminate(nsiId)
      time.sleep(0.1)
      thread_ns_termination.start()
      
      value = 200
    elif (instan_time < termin_time):                       # TODO: manage future termination orders
      jsonNSI['terminateTime'] = str(termin_time)
      repo_responseStatus = nsi_repo.update_nsi(jsonNSI, nsiId)
      value = 200
    else:
      repo_responseStatus = {"error":"Wrong value: 0 for instant termination or date time later than "+NSI.instantiateTime+", to terminate in the future."}
      value = 400

    return (repo_responseStatus, value)
  else:
    return ('{"error":"There is no NSIR in the db."}', 500)

# Updates a NSI being terminated with the latest informationg coming from the MANO/GK.
def update_terminating_nsi(nsiId, request_json):
  LOG.info("NSI_MNGR: get the specific NSI to update the right service information.")
  time.sleep(0.1)
  jsonNSI = nsi_repo.get_saved_nsi(nsiId)
  if (jsonNSI):
    # starts the thread to update termination info within the services
    thread_update_slice_termination = update_slice_termination(nsiId, request_json)
    time.sleep(0.1)
    thread_update_slice_termination.start()
    return (jsonNSI, 200)
  else:
    return ('{"error":"There is no NSIR in the db."}', 500)

# Checks if there is any other NSI based on a NST. If not, changes the nst usageStatus parameter to "NOT_IN_USE"
def removeNSIinNST(nstId):
  nsis_list = nsi_repo.get_all_saved_nsi()
  all_nsis_terminated = True
  for nsis_item in nsis_list:
    if (nsis_item['nst-ref'] == nstd_id and nsis_item['nsi-status'] == "INSTANTIATED" or nsis_item['nsi-status'] == "INSTANTIATING" or nsis_item['nsi-status'] == "READY"):
        all_nsis_terminated = False
        break;
    else:
      pass

  if (all_nsis_terminated):
    nst_descriptor = nst_catalogue.get_saved_nst(nstId)
    nst_json = nst_descriptor['nstd']
    if (nst_json['usageState'] == "IN_USE"):
      nstParameter2update = "usageState=NOT_IN_USE"
      updatedNST_jsonresponse = nst_catalogue.update_nst(nstParameter2update, nstId)
  

############################################ NSI GET SECTION ############################################
# Gets one single NSI item information
def get_nsi(nsiId):
  LOG.info("NSI_MNGR: Retrieving NSI with id: " +str(nsiId))
  nsirepo_jsonresponse = nsi_repo.get_saved_nsi(nsiId)
  if (nsirepo_jsonresponse):
    return (nsirepo_jsonresponse, 200)
  else:
    return ('{"error":"There is no NSIR in the db."}', 500)

# Gets all the existing NSI items
def get_all_nsi():
  LOG.info("NSI_MNGR: Retrieve all existing NSIs")
  nsirepo_jsonresponse = nsi_repo.get_all_saved_nsi()
  if (nsirepo_jsonresponse):
    return (nsirepo_jsonresponse, 200)
  else:
    return ('{"error":"There are no NSIR in the db."}', 500)