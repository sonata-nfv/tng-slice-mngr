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
## Objctive: reads subnets list in Network Slice Instance (NSI) and sends requests2GTK to instantiate them 
## Params: NSI - nsi created with the parameters given by the user and the NST saved in catalogues.
class thread_ns_instantiate(Thread):
  def __init__(self, NSI, nst_object):
    Thread.__init__(self)
    self.NSI = NSI
    self.nst_object
  
  def send_networks_creation_request(self):
    LOG.info("NSI_MNGR: Requesting slice networks creationg to the GTK.")
    time.sleep(0.1)

    # creates the 1st json level structure {instance_id: ___, vim_list: []}
    network_data = {}
    network_data['instance_id'] = self.NSI['id']    # uses the slice id for its networks
    network_data['vim_list'] = []

    # creates the elements of the 2nd json level structure {uuid:__, virtual_links:[]} and adds them into the 'vim_list'
    for vldr_item in self.NSI['vldr-list']:
      vim_item = {}
      vim_item['uuid'] = vldr_item['vimAccountId']
      vim_item['virtual_links'] = []
      if not network_data['vim_list']:
        network_data['vim_list'].append(vim_item)
      else:
        if vim_item not in network_data['vim_list']:
          network_data['vim_list'].append(vim_item)
        else:
          continue
    
    # creates the elements of the 3rd json level struture {id: ___, access: bool} and adds them into the 'virtual_links'
    for vldr_item in self.NSI['vldr-list']:
      for vim_item in network_data['vim_list']:
        if vldr_item['vimAccountId'] == vim_item['uuid']:
          virtual_link_item = {}
          virtual_link_item['id'] = vldr_item['vim-net-id']
          virtual_link_item['access'] = "true"          #TODO: how do I decide wheater is Ture or False??
          if not vim_item['virtual_links']:
            vim_item['virtual_links'].append(virtual_link_item)
          else:
            if virtual_link_item not in vim_item['virtual_links']:
              vim_item['virtual_links'].append(virtual_link_item)
            else:
              continue

    LOG.info("NSI_MNGR_Instantiate: json to create networks: " + str(network_data))
    time.sleep(0.1)

    # calls the mapper to sent the networks creation requests to the GTK (and this to the IA)
    nets_creation_response = mapper.create_vim_network(network_data)

  def send_instantiation_requests(self):
    LOG.info("NSI_MNGR_Instantiate: Instantiating Services")
    time.sleep(0.1)
    
    for nsr_item in self.NSI['nsr-list']:
      # Preparing the dict to stitch the NS to the Networks (VLDs)
      '''
      {
        "mapping": {
          "network_functions":[
            {"vnf_id": "nsd_vnfd_id", "vim_id": "datacenter_id"}
          ],
          "virtual_links":[
            {
                "vl_id": "nsd_vld_id", "external_net": "nsi_vld_id", "vim_id": "datacenter_id"
            }
          ]
        }
      }
      '''
      mapping = {}
      network_functions_list = []
      virtual_links_list = []
      repo_item = mapper.get_nsd_list(nsr_item['subnet-nsdId-ref'])
      nsd_item = repo_item['nsd']

      ## Creates the 'network_functions' object
      for vnf_item in nsd_item['network_functions']:
        net_funct = {}
        net_funct['vnf_id'] = vnf_item['vnf_id']
        net_funct['vim_id'] = nsr_item['vimAccountId']  #TODO: FUTURE think about placement
        network_functions_list.append(net_funct)
      
      mapping['network_functions'] = network_functions_list
      LOG.info("NSI_MNGR_Instantiate: mapping json to stitch NS_2_nets" +str(mapping))
      time.sleep(0.1)
      
      ## Creates the 'virtual_links' object
      # for each nsr, checks its vlds and looks for its infortmation in vldr-list
      for vld_nsr_item in nsr_item['vld']:
        vld_ref = vld_nsr_item['vld_ref']
        for vldr_item in self.NSI['vldr-list']:
          # vld connected to the nsd found, keeps the external network
          if vldr_item['id'] ==  vld_ref:
            external_net = vldr_item['vim-net-id']
            LOG.info("NSI_MNGR_Instantiate: external_net" +str(external_net))
            time.sleep(0.1)
            # using the ns connection point references to fins the internal NS vld
            for ns_cp_item in vldr_item['ns-conn-point-ref']:
              subnet_key = nsr_item['subnet-ref']
              # if the subnet in the vld correspond to the current nsr keep going...
              if subnet_key in ns_cp_item.keys():
                ns_cp_ref = ns_cp_item[subnet_key]
                # gets the right nsd to find the internal NS vld to which the CP is connected
                nsd_catalogue_object = mapper.get_nsd(nsr-item['subnet-nsdId-ref'])
                nsd_virtual_links_list = nsd_catalogue_object['nsd']['virtual_links']
                for nsd_vl_item in nsd_virtual_links_list:
                  for ns_cp_ref_item in nsd_vl_item['connection_points_reference']:
                    if ns_cp_ref_item == ns_cp_ref:
                      vl_id = nsd_vl_item['id']
                      LOG.info("NSI_MNGR_Instantiate: vl_id" +str(vl_id))
                      time.sleep(0.1)
                      break 
                break
            break 
        virt_link = {}
        virt_link['vl_id'] = vl_id
        virt_link['external_net'] = external_net
        virt_link['vim_id'] = nsr_item['vimAccountId']  #TODO: FUTURE think about placement
        virtual_links_list.append(virt_link)

      mapping['virtual_links'] = virtual_links_list
      LOG.info("NSI_MNGR_Instantiate: mapping json to stitch NS_2_nets" +str(mapping))
      time.sleep(0.1)

      # TODO: SHARED FUNCT -> if the nsr_item is shared and already has a nsrId = DON'T SEND REQUEST
      # Sending Network Services Instantiation requests
      data = {}
      data['name'] = nsr_item['nsrName']
      data['service_uuid'] = nsr_item['subnet-nsdId-ref']
      data['callback'] = "http://tng-slice-mngr:5998/api/nsilcm/v1/nsi/"+str(self.NSI['id'])+"/instantiation-change"
      #data['ingresses'] = []
      #data['egresses'] = []
      #data['blacklist'] = []
      if (nsr_item['sla-ref'] != "None"):
        data['sla_id'] = nsr_item['sla-ref']
      data['mapping'] = mapping

      LOG.info("NSI_MNGR_Instantiate: this is what GTK receives: " +str(data))
      time.sleep(0.1)
      # requests to instantiate NSI services to the SP
      #instantiation_response = mapper.net_serv_instantiate(data)

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
    self.send_networks_creation_request()
    
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
    
    #TODO: if deployment_timeout expires, notify it with error as status
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
  def __init__(self,NSI):
    Thread.__init__(self)
    self.NSI = NSI
  
  def send_termination_requests(self):
    LOG.info("NSI_MNGR_Terminate: Terminating Services")
    time.sleep(0.1)
    for nsr_item in self.NSI['nsr-list']:
      if (nsr_item['working-status'] != "ERROR"):
        data = {}
        data["instance_uuid"] = str(nsr_item["nsrId"])
        data["request_type"] = "TERMINATE_SERVICE"
        data['callback'] = "http://tng-slice-mngr:5998/api/nsilcm/v1/nsi/"+str(self.NSI['id'])+"/terminate-change"

        termination_response = mapper.net_serv_terminate(data)

  def send_networks_removal_request(self):
    LOG.info("NSI_MNGR: Requesting slice networks removal to the GTK.")

    # creates the 1st json level structure {instance_id: ___, vim_list: []}
    network_data = {}
    network_data['instance_id'] = self.NSI['id']    # uses the slice id for its networks
    network_data['vim_list'] = []

    # creates the elements of the 2nd json level structure {uuid:__, virtual_links:[]} and adds them into the 'vim_list'
    for vldr_item in self.NSI['vldr-list']:
      vim_item = {}
      vim_item['uuid'] = vldr_item['vimAccountId']
      vim_item['virtual_links'] = []
      if not network_data['vim_list']:
        network_data['vim_list'].append(vim_item)
      else:
        if vim_item not in network_data['vim_list']:
          network_data['vim_list'].append(vim_item)
        else:
          continue
    
    # creates the elements of the 3rd json level struture {id: ___, access: bool} and adds them into the 'virtual_links'
    for vldr_item in self.NSI['vldr-list']:
      for vim_item in network_data['vim_list']:
        if vldr_item['vimAccountId'] == vim_item['uuid']:
          virtual_link_item = {}
          virtual_link_item['id'] = vldr_item['vim-net-id']
          if not vim_item['virtual_links']:
            vim_item['virtual_links'].append(virtual_link_item)
          else:
            if virtual_link_item not in vim_item['virtual_links']:
              vim_item['virtual_links'].append(virtual_link_item)
            else:
              continue

    LOG.info("NSI_MNGR_Instantiate: json to remove networks: " + str(network_data))

    # calls the mapper to sent the networks creation requests to the GTK (and this to the IA)
    #nets_creation_response = mapper.delete_vim_network(network_data)

  def update_nsi_notify_terminate(self):
    mutex_slice2db_access.acquire()
    try:
      LOG.info("NSI_MNGR_Notify: Slice termination Notification to GTK.")
      time.sleep(0.1)
      jsonNSI = nsi_repo.get_saved_nsi(self.NSI['id'])
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
      repo_responseStatus = nsi_repo.update_nsi(jsonNSI, self.NSI['id'])

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
    # deployment_timeout = 2 * 3600   # Two hours
    deployment_timeout = 1800         # 30 minutes  # TODO: remove once it works without errors
    while deployment_timeout > 0:
      LOG.info("Waiting all services are terminated or error...")
      # Check ns instantiation status
      nsi_terminated = True
      jsonNSI = nsi_repo.get_saved_nsi(self.NSI['id'])
      for nsr_item in jsonNSI['nsr-list']: 
        if nsr_item['working-status'] not in ["TERMINATED", "ERROR", "READY"]:
          nsi_terminated = False
      
      # if all services are instantiated or error, break the while loop to notify the GTK
      if nsi_terminated:
        LOG.info("All service termination are ready!")
        break
  
      time.sleep(10)
      deployment_timeout -= 10
    
    if deployment_timeout <= 0:
      raise LCMException("Timeout waiting nsi to be terminated. nsi_id={}".format(self.NSI['id']))
    
    # TODO:Sends all the requests to create all the VLDs within the slice
    self.send_networks_removal_request()

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

  # validate if there is any NSTD
  LOG.info("NSI_MNGR: Checking if the NSTD exists...")
  if not catalogue_response:
    return_msg = {}
    return_msg['error'] = "There is NO NSTd with this uuid in the DDBB."
    return return_msg, 400

  # check if there is any other nsir with the same name, vendor, nstd_version
  LOG.info("NSI_MNGR: Checking there is no duplicated NSI.")
  nsirepo_jsonresponse = nsi_repo.get_all_saved_nsi()
  if nsirepo_jsonresponse:
    for nsir_item in nsirepo_jsonresponse:
      if (nsir_item["name"] == nsi_json['name'] and nsir_item["nst-version"] == nst_json['version'] and \
        nsir_item["vendor"] == nst_json['vendor']):
        error_msg = '{"error":"There is already a slice with thie name/version/vendor. Change one of the values."}'
        return (error_msg, 500)

  # get the VIMs information registered to the SP
  # vims_list = mapper.get_vims_info()
  # if not vims_list['vim_list']:         # validates if there's no vim to return a msg.
  #   return_msg = {}
  #   return_msg['error'] = "Not found any VIM information."
  #   return return_msg, 500
  # LOG.info("NSI_MNGR: VIMs list information: " +str(vims_list))
  
  #TODO: improve placement
  # main_datacenter = vims_list['vim_list'][0]['vim_uuid']
  main_datacenter = str(uuid.uuid4())
  LOG.info("NSI_MNGR: VIMs list information: " +str(main_datacenter))
  
  # creates NSI with the received information
  LOG.info("NSI_MNGR: Creating NSI basic structure.")
  new_nsir = add_basic_nsi_info(nst_json, nsi_json, main_datacenter)
  
  # adds the VLD information within the NSI record
  LOG.info("NSI_MNGR:  Adding vlds into the NSI structure.")
  new_nsir = add_vlds(new_nsir, nst_json['slice_vld'])
  
  # adds the NetServices (subnets) information within the NSI record
  LOG.info("NSI_MNGR:  Adding subnets into the NSI structure.")
  new_nsir = add_subnets(new_nsir, nst_json, nsi_json)

  # saving the NSI into the repositories
  LOG.info("NSI_MNGR:  Saving the NSIr into resporitories.")
  nsirepo_jsonresponse = nsi_repo.safe_nsi(new_nsir)

  # starts the thread to instantiate while sending back the response
  #thread_ns_instantiation = thread_ns_instantiate(new_nsir, nst_json)
  #thread_ns_instantiation.start()

  return nsirepo_jsonresponse, 201

# Basic NSI structure
def add_basic_nsi_info(nst_json, nsi_json, main_datacenter):
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
  nsir_dict['datacenter'] = main_datacenter
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
def add_vlds(new_nsir, nst_vld_list):
  vldr_list = []
  for vld_item in nst_vld_list:
    vld_record = {}
    vld_record['id'] = vld_item['id']
    vld_record['name'] = vld_item['name']
    vld_record['vimAccountId'] = new_nsir['datacenter']  #TODO: improve with placement
    vld_record['vim-net-id']  = new_nsir['name'] + "." + vld_item['name'] + ".net." + str(uuid.uuid4())
    if 'mgmt-network' in vld_item.keys():
      vld_record['mgmt-network'] = True
    vld_record['type'] = vld_item['type']
    #vld_record['root-bandwidth']
    #vld_record['leaf-bandwidth']                   #TODO: check how to use this 4 parameters
    #vld_record['physical-network']
    #vld_record['segmentation_id']
    vld_record['vld-status'] = 'INACTIVE'
    
    cp_refs_list = []
    for cp_ref_item in vld_item['nsd-connection-point-ref']:
      cp_dict = {}
      cp_dict[cp_ref_item['subnet-ref']] = cp_ref_item['nsd-cp-ref']
      cp_refs_list.append(cp_dict)
    vld_record['ns-conn-point-ref'] = cp_refs_list
    
    vld_record['shared-nsrs-list'] = []   # this is filled when a shared service is instantiated on this VLD
    #vld_record['requestId'] = " "

    vldr_list.append(vld_record)
  
  new_nsir['vldr-list'] = vldr_list
  return new_nsir

# Adds the basic subnets information to the NSI record
def add_subnets(new_nsir, nst_json, request_nsi_json):
  nsr_list = []                         # empty list to add all the created slice-subnets
  serv_seq = 1                          # to put in order the services within a slice in the portal
  
  for subnet_item in nst_json["slice_ns_subnets"]:
    subnet_record = {}
    subnet_record['nsrName'] = new_nsir['name'] + "-" + subnet_item['id'] + "-" + str(serv_seq)
    
    # TODO:  SHARED FUNCT -> check if the service is shared, then look if there is any other nsi ...
    # ... with that same service (uuid or name/vendor/version) instantiated and take its nsrId.
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
    
    # adding the vld id where each subnet is connected to
    subnet_vld_list = []
    for vld_item in nst_json["slice_vld"]:
      for nsd_cp_item in vld_item['nsd-connection-point-ref']:
        if subnet_item['id'] == nsd_cp_item['subnet-ref']:
          subnet_vld_item = {}
          subnet_vld_item['vld-ref'] = vld_item['id']
          subnet_vld_list.append(subnet_vld_item)
          break #TODO: is it be possible that a subnet has 2 connection points to the same VLD??

    subnet_record['vld'] = subnet_vld_list

    nsr_list.append(subnet_record)
    serv_seq = serv_seq + 1
  
  new_nsir['nsr-list'] = nsr_list
  return new_nsir

# Start to instantiate a specific nsi with the current vim_list infoAdds the basic subnets information to the NSI record
def start_instantiating_nsi(nsiId, request_json):

  return

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

      repo_responseStatus = nsi_repo.update_nsi(jsonNSI, nsiId)

      # starts the thread to terminate while sending back the response
      thread_ns_termination = thread_ns_terminate(jsonNSI)
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

  #TODO: validate if there are nsis to return it as error

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
    return_msg = {}
    return_msg['msg'] = "There are no NSIR with this uuid in the db."
    return (return_msg, 200)

# Gets all the existing NSI items
def get_all_nsi():
  LOG.info("NSI_MNGR: Retrieve all existing NSIs")
  nsirepo_jsonresponse = nsi_repo.get_all_saved_nsi()
  if (nsirepo_jsonresponse):
    return (nsirepo_jsonresponse, 200)
  else:
    return_msg = {}
    return_msg['msg'] = "There are no NSIR in the db."
    return (return_msg, 200)