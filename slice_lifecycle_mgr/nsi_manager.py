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
  def __init__(self, NSI):
    Thread.__init__(self)
    self.NSI = NSI
  
  def send_networks_creation_request(self):
    LOG.info("NSI_MNGR: Requesting slice networks creation to the GTK.")
    time.sleep(0.1)

    # creates the 1st json level structure {instance_id: ___, vim_list: []}
    network_data = {}
    network_data['instance_id'] = self.NSI['id']
    network_data['vim_list'] = []

    # creates the elements of the 2nd json level structure {uuid:__, virtual_links:[]} and ...
    # ...adds them into the 'vim_list'
    for vldr_item in self.NSI['vldr-list']:
      if vldr_item['vld-status'] == "INACTIVE":              # to avoid create already existing networks
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
    
    # creates the elements of the 3rd json level struture {id: ___, access: bool} and...
    # ... adds them into the 'virtual_links'
    for vldr_item in self.NSI['vldr-list']:
      if vldr_item['vld-status'] == "INACTIVE":              # to avoid create already existing networks
        for vim_item in network_data['vim_list']:
          if vldr_item['vimAccountId'] == vim_item['uuid']:
            virtual_link_item = {}
            virtual_link_item['id'] = vldr_item['vim-net-id']
            virtual_link_item['access'] = vldr_item['access_net']
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

    return nets_creation_response

  def send_instantiation_requests(self, nsr_item):
    LOG.info("NSI_MNGR_Instantiate: Instantiating Services")
    time.sleep(0.1)
    
    #for nsr_item in self.NSI['nsr-list']:
    # Sending Network Services Instantiation requests
    data = {}
    data['name'] = nsr_item['nsrName']
    data['service_uuid'] = nsr_item['subnet-nsdId-ref']
    data['callback'] = "http://tng-slice-mngr:5998/api/nsilcm/v1/nsi/"+str(self.NSI['id'])+"/instantiation-change"

    # Creates the extra parameters for the requests: slice-vld, ingresses, egresses, SLA
    if self.NSI.get('vldr-list'):
      # Preparing the dict to stitch the NS to the Networks (VLDs)
      mapping = {}
      network_functions_list = []
      virtual_links_list = []
      repo_item = mapper.get_nsd(nsr_item['subnet-nsdId-ref'])
      nsd_item = repo_item['nsd']
      
      ## 'network_functions' object creation
      for vnf_item in nsd_item['network_functions']:
        net_funct = {}
        net_funct['vnf_id'] = vnf_item['vnf_id']
        net_funct['vim_id'] = nsr_item['vimAccountId']  #TODO: FUTURE think about placement
        network_functions_list.append(net_funct)
      mapping['network_functions'] = network_functions_list
      
      ## 'virtual_links' object creation
      # for each nsr, checks its vlds and looks for its infortmation in vldr-list
      for vld_nsr_item in nsr_item['vld']:
        vld_ref = vld_nsr_item['vld-ref']
        for vldr_item in self.NSI['vldr-list']:
          # vld connected to the nsd found, keeps the external network
          if vldr_item['id'] ==  vld_ref:
            external_net = vldr_item['vim-net-id']
            # using the ns connection point references to fins the internal NS vld
            for ns_cp_item in vldr_item['ns-conn-point-ref']:
              subnet_key = nsr_item['subnet-ref']
              # if the subnet in the vld correspond to the current nsr keep going...
              if subnet_key in ns_cp_item.keys():
                ns_cp_ref = ns_cp_item[subnet_key]
                # gets the right nsd to find the internal NS vld to which the CP is connected
                nsd_catalogue_object = mapper.get_nsd(nsr_item['subnet-nsdId-ref'])
                nsd_virtual_links_list = nsd_catalogue_object['nsd']['virtual_links']
                for nsd_vl_item in nsd_virtual_links_list:
                  for ns_cp_ref_item in nsd_vl_item['connection_points_reference']:
                    if ns_cp_ref_item == ns_cp_ref:
                      vl_id = nsd_vl_item['id']
                      break 
                break
            break 
        virt_link = {}
        virt_link['vl_id'] = vl_id
        virt_link['external_net'] = external_net
        virt_link['vim_id'] = nsr_item['vimAccountId']  #TODO: FUTURE think about placement
        virtual_links_list.append(virt_link)
      mapping['virtual_links'] = virtual_links_list
      data['mapping'] = mapping

    if (nsr_item['sla-ref'] != "None"):
      data['sla_id'] = nsr_item['sla-ref']
    else:
      data['sla_id'] = ""
    
    if nsr_item['ingresses']:
      data['ingresses'] = nsr_item['ingresses']
    else:
      data['ingresses'] = []
    
    if nsr_item['egresses']:
      data['egresses'] = nsr_item['egresses']
    else:
      data['egresses'] = []
    # data['blacklist'] = []

    LOG.info("NSI_MNGR_Instantiate: this is what GTK receives: " +str(data))
    time.sleep(0.1)
    # requests to instantiate NSI services to the SP
    instantiation_response = mapper.net_serv_instantiate(data)
    LOG.info("NSI_MNGR_Instantiate: GTK instantiation_response: " +str(instantiation_response))
    time.sleep(0.1)
    return instantiation_response

  def update_nsi_notify_instantiate(self):
    mutex_slice2db_access.acquire()
    try:
      LOG.info("NSI_MNGR_Notify: Slice instantitaion Notification to GTK.")
      time.sleep(0.1)
      jsonNSI = nsi_repo.get_saved_nsi(self.NSI['id'])
      jsonNSI["id"] = jsonNSI["uuid"]
      del jsonNSI["uuid"]


      # updates the slice information before notifying the GTK
      if jsonNSI['nsi-status'] == "INSTANTIATING":
        jsonNSI['nsi-status'] = "INSTANTIATED"

        # validates if any service has error status to apply it to the slice status
        for service_item in jsonNSI['nsr-list']:
          if service_item['working-status'] in ["ERROR", "INSTANTIATING"]:
            service_item['working-status'] = 'ERROR'
            jsonNSI['nsi-status'] = "ERROR"

        # updates NetSlice template usageState
        if(jsonNSI['nsi-status'] == "INSTANTIATED"):
          nst_descriptor = nst_catalogue.get_saved_nst(jsonNSI['nst-ref'])
          if (nst_descriptor['nstd'].get('usageState') == "NOT_IN_USE"):
            nstParameter2update = "usageState=IN_USE"
            updatedNST_jsonresponse = nst_catalogue.update_nst(nstParameter2update, jsonNSI['nst-ref'])
      else:
        # this only happens if networks are not created, NS get "NOT_INSTANTIATED" status
        for service_item in jsonNSI['nsr-list']:
          service_item['working-status'] == "NOT_INSTANTIATED"
      
      # sends the updated NetSlice instance to the repositories
      jsonNSI['updateTime'] = str(datetime.datetime.now().isoformat())
      repo_responseStatus = nsi_repo.update_nsi(jsonNSI, self.NSI['id'])

    finally:
      # release the mutex for other threads
      mutex_slice2db_access.release()
      
      # creates a thread with the callback URL to advise the GK this slice is READY
      slice_callback = jsonNSI['sliceCallback']
      json_slice_info = {}
      json_slice_info['status'] = jsonNSI['nsi-status']
      json_slice_info['updateTime'] = jsonNSI['updateTime']

      thread_response = mapper.sliceUpdated(slice_callback, json_slice_info)
      LOG.info("NSI_MNGR_Notify: THREAD FINISHED, GTK notified with status: " +str(thread_response[1]))

  def run(self):
    # set to true in order to instantiates NSs in case there are no slice_vld to create
    network_ready = True

    # acquires mutex to have unique access to the nsi (rpositories)
    mutex_slice2db_access.acquire()
    try:
      # enters only if there are vld/networks to create and deploy
      if self.NSI.get('vldr-list'):
        # sends all the requests to create all the VLDs (networks) within the slice
        networks_response = self.send_networks_creation_request()
        LOG.info("NSI_MNGR: network_response: " +str(networks_response))
        time.sleep(0.1)

        # checks that all the networks are created. otherwise, (network_ready = False) services are not requested
        if networks_response['status'] == 'COMPLETED':
          LOG.info("NSI_MNGR: NETWORKS CREATED")
          time.sleep(0.1)
          vld_status = "ACTIVE"
        else:
          LOG.info("NSI_MNGR: networks NOT created")
          time.sleep(0.1)
          vld_status = "ERROR"
          self.NSI['nsi-status'] = "ERROR"
          self.NSI['errorLog'] = networks_response['error']
          for nss_item in self.NSI['nsr-list']:
            nss_item['working-status'] = "NOT_INSTANTIATED"
          
          # if networks are not created, no need to request NS instantiations
          network_ready = False

        for vld_item in self.NSI['vldr-list']:
          vld_item['vld-status'] = vld_status

      if network_ready:
        # Sends all the requests to instantiate the NSs within the slice
        for nsr_item in self.NSI['nsr-list']:
          if (nsr_item['isshared'] == False or nsr_item['isshared'] and nsr_item['working-status'] == "NEW"):
            instantiation_resp = self.send_instantiation_requests(nsr_item)
            if instantiation_resp[1] == 201:
              nsr_item['working-status'] == 'INSTANTIATING'
        
        # sends the updated NetSlice instance to the repositories
        repo_responseStatus = nsi_repo.update_nsi(self.NSI, self.NSI['id'])
    
    finally: 
      # releases mutex for any other thread to acquire it
      mutex_slice2db_access.release()

      # Waits until all the NSs are instantiated/ready or error
      LOG.info("Processing services instantiations...")
      #deployment_timeout = 2 * 3600   # Two hours
      deployment_timeout = 900   # 15min   #TODO: mmodify for the reviews
      while deployment_timeout > 0:
        # Check ns instantiation status
        nsi_instantiated = True
        jsonNSI = nsi_repo.get_saved_nsi(self.NSI['id'])
        for nsr_item in jsonNSI['nsr-list']: 
          if nsr_item['working-status'] not in ["INSTANTIATED", "ERROR", "READY"]:
            nsi_instantiated = False
        
        # if all services are instantiated or error, break the while loop to notify the GTK
        if nsi_instantiated:
          LOG.info("All service instantiations requests processed!")
          break
    
        time.sleep(15)
        deployment_timeout -= 15
      
    LOG.info("NSI_MNGR_Notify: Updating and notifying GTK")    
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
          
          # check if there an id of the instantiation within the VIM
          if (self.request_json['instance_uuid'] != None):
            service_item['nsrId'] = self.request_json['instance_uuid']
            
            # updates shared-nsrs-list in the specific vlds where the shared service is linked
            if service_item['isshared']:
              for nsr_vld_item in service_item['vld']:
                for vld_vldr_item in jsonNSI['vldr-list']:
                  if vld_vldr_item['id'] == nsr_vld_item['vld-ref']:
                    vld_vldr_item['shared-nsrs-list'].append(service_item['nsrId'])

          if (self.request_json['status'] == "READY"):
            service_item['working-status'] = "INSTANTIATED"
          else:
            service_item['working-status'] = self.request_json['status']
                    
          LOG.info("NSI_MNGR_Update: Service updated")
          time.sleep(0.1)
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
      if (nsr_item['working-status'] == "TERMINATING"):
        data = {}
        data["instance_uuid"] = str(nsr_item["nsrId"])
        data["request_type"] = "TERMINATE_SERVICE"
        data['callback'] = "http://tng-slice-mngr:5998/api/nsilcm/v1/nsi/"+str(self.NSI['id'])+"/terminate-change"

        LOG.info("NSI_MNGR_Terminate: GTK receive termination data: " +str(data))
        time.sleep(0.1)
        # requests to terminate NSI services
        termination_response = mapper.net_serv_terminate(data)
        LOG.info("NSI_MNGR_Terminate: termination_response: " +str(termination_response))
        time.sleep(0.1)

  def send_networks_removal_request(self):
    LOG.info("NSI_MNGR: Requesting slice networks removal to the GTK.")
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
          if not vim_item['virtual_links']:
            vim_item['virtual_links'].append(virtual_link_item)
          else:
            if virtual_link_item not in vim_item['virtual_links']:
              vim_item['virtual_links'].append(virtual_link_item)
            else:
              continue

    LOG.info("NSI_MNGR_Instantiate: json to remove networks: " + str(network_data))
    time.sleep(0.1)

    # calls the mapper to sent the networks creation requests to the GTK (and this to the IA)
    nets_removal_response = mapper.delete_vim_network(network_data)
    return nets_removal_response

  def update_nsi_notify_terminate(self):
    mutex_slice2db_access.acquire()
    try:
      LOG.info("NSI_MNGR_Notify: Slice termination Notification to GTK.")
      time.sleep(0.1)
      jsonNSI = nsi_repo.get_saved_nsi(self.NSI['id'])
      jsonNSI["id"] = jsonNSI["uuid"]
      del jsonNSI["uuid"]

      # updates nsir fields
      jsonNSI['updateTime'] = jsonNSI['terminateTime']
      if jsonNSI['nsi-status'] == "TERMINATING":
        jsonNSI['nsi-status'] = "TERMINATED"
      
      # validates if any service has error status to apply it to the slice status
      for service_item in jsonNSI['nsr-list']:
        if (service_item['working-status'] == "ERROR"):
          jsonNSI['nsi-status'] = "ERROR"
          jsonNSI['errorLog'] = "Network Slice termination not done due to a service termination error."
          break

      # sends the updated nsi to the repositories
      repo_responseStatus = nsi_repo.update_nsi(jsonNSI, self.NSI['id'])

      # updates NetSlice template usageState if no other nsi is instantiated/ready
      nsis_list = nsi_repo.get_all_saved_nsi()
      all_nsis_terminated = True
      for nsis_item in nsis_list:
        if (nsis_item['nst-ref'] == self.NSI['nst-ref'] and nsis_item['nsi-status'] in ["INSTANTIATED", "INSTANTIATING", "READY"]):
            all_nsis_terminated = False
            break
      
      if (all_nsis_terminated):
        nst_descriptor = nst_catalogue.get_saved_nst(self.NSI['nst-ref'])
        nst_json = nst_descriptor['nstd']
        if (nst_json['usageState'] == "IN_USE"):
          nstParameter2update = "usageState=NOT_IN_USE"
          updatedNST_jsonresponse = nst_catalogue.update_nst(nstParameter2update, self.NSI['nst-ref'])

    finally:
      # release the mutex for other threads
      mutex_slice2db_access.release()

      # sends the request to notify the GTK the slice is READY
      slice_callback = jsonNSI['sliceCallback']
      json_slice_info = {}
      json_slice_info['status'] = jsonNSI['nsi-status']
      json_slice_info['updateTime'] = jsonNSI['updateTime']

      thread_response = mapper.sliceUpdated(slice_callback, json_slice_info)
      LOG.info("NSI_MNGR_Notify: THREAD FINISHED, GTK notified with status: " +str(thread_response[1]))

  def run(self):
    # Sends all the requests to instantiate the NSs within the slice
    self.send_termination_requests()

    # Waits until all the NSs are terminated/ready or error
    LOG.info("Processing services terminations...")
    # deployment_timeout = 2 * 3600   # Two hours
    deployment_timeout = 900         # 15 minutes  #TODO: mmodify for the reviews
    while deployment_timeout > 0:
      time.sleep(0.1)
      # Check ns instantiation status
      nsi_terminated = True
      jsonNSI = nsi_repo.get_saved_nsi(self.NSI['id'])
      for nsr_item in jsonNSI['nsr-list']: 
        if nsr_item['working-status'] not in ["TERMINATED", "ERROR", "READY"]:
          nsi_terminated = False
      
      # if all services are instantiated or error, break the while loop to notify the GTK
      if nsi_terminated:
        LOG.info("All service terminations requests processed!")
        time.sleep(0.1)
        break
  
      time.sleep(15)
      deployment_timeout -= 15
    
    # enters only if there are vld/networks to create and deploy
    if self.NSI.get('vldr-list'):
      # requests to remove the created networks for the current slice
      net_removal_response = self.send_networks_removal_request()

      try:
        # acquires mutex to have unique access to the nsi (rpositories)
        mutex_slice2db_access.acquire()
        temp_nsi = nsi_repo.get_saved_nsi(self.NSI['id'])
        temp_nsi["id"] = temp_nsi["uuid"]
        del temp_nsi["uuid"]

        # checks that all the networks are created. otherwise, (network_ready = False) services are not requested
        if net_removal_response['status'] in ['COMPLETED']:
            vld_status = "INACTIVE"
        else:
            vld_status = "ERROR"
            temp_nsi['nsi-status'] = "ERROR"
            temp_nsi['errorLog'] = net_removal_response['message']
        
        for vld_item in temp_nsi['vldr-list']:
          vld_item['vld-status'] = vld_status
        
        # sends the updated NetSlice instance to the repositories
        repo_responseStatus = nsi_repo.update_nsi(temp_nsi, self.NSI['id'])

      finally:
        # releases mutex for any other thread to acquire it
        mutex_slice2db_access.release()

    # Notifies the GTK that the Network Slice termination process is done (either complete or error)
    LOG.info("NSI_MNGR_Notify: Updating and notifying terminate to GTK") 
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
      mutex_slice2db_access.release()


################################ NSI CREATION & INSTANTIATION SECTION ##################################
# 2 steps: create_nsi (with its internal functions) and update_instantiating_nsi
# Network Slice Instance Object Creation
def create_nsi(nsi_json):
  LOG.info("NSI_MNGR: Creates and Instantiates a new NSI.")
  time.sleep(0.1)
  nstId = nsi_json['nstId']
  catalogue_response = nst_catalogue.get_saved_nst(nstId)
  if catalogue_response.get('nstd'):
    nst_json = catalogue_response['nstd']
  else:
    return catalogue_response, catalogue_response['http_code']

  # validate if there is any NSTD
  if not catalogue_response:
    return_msg = {}
    return_msg['error'] = "There is NO NSTd with this uuid in the DDBB."
    return return_msg, 400

  # check if there is another nsir with the same name AND based to the same NSTd (uuid, version, vendor)
  nsirepo_jsonresponse = nsi_repo.get_all_saved_nsi()
  if nsirepo_jsonresponse:
    for nsir_item in nsirepo_jsonresponse:
      if (nsir_item["name"] == nsi_json['name'] and nsir_item["nst-ref"] == nst_json['uuid'] and \
          nsir_item["nst-version"] == nst_json['version'] and nsir_item["vendor"] == nst_json['vendor']):
        return_msg = {}
        return_msg['error'] = "There is already a slice with thie name and based to the selected NSTd (id/name/vendor/version)."
        return (return_msg, 400)

  # Network Slice Placement  
  vim_nsi = nsi_placement()               #TODO: improve internal logic (resources?)
  if vim_nsi[1] == 500:
    return vim_nsi
   
  # creates NSI with the received information
  LOG.info("NSI_MNGR: Creating NSI basic structure.")
  time.sleep(0.1)
  new_nsir = add_basic_nsi_info(nst_json, nsi_json, vim_nsi[0]) #TODO: improve placement
  
  # adds the NetServices (subnets) information within the NSI record
  LOG.info("NSI_MNGR:  Adding subnets into the NSI structure.")
  time.sleep(0.1)
  new_nsir = add_subnets(new_nsir, nst_json, nsi_json)
  LOG.info("NSI_MNGR:  After adding subnets:" + str(new_nsir))
  time.sleep(0.1)
  # adds the VLD information within the NSI record
  if nst_json.get("slice_vld"):
    LOG.info("NSI_MNGR:  Adding vlds into the NSI structure.")
    time.sleep(0.1)
    new_nsir = add_vlds(new_nsir, nst_json)
    LOG.info("NSI_MNGR:  After adding vlds:" + str(new_nsir))
    time.sleep(0.1)
  
  # saving the NSI into the repositories
  nsirepo_jsonresponse = nsi_repo.safe_nsi(new_nsir)

  if nsirepo_jsonresponse[1] == 200:
    # starts the thread to instantiate while sending back the response
    thread_ns_instantiation = thread_ns_instantiate(new_nsir)
    thread_ns_instantiation.start()
  else:
    error_msg = nsirepo_jsonresponse[0]
    new_nsir['errorLog'] = error_msg['message']
    nsirepo_jsonresponse = new_nsir
  
  return nsirepo_jsonresponse
  
# TODO: improve placement logic
# does the placement of all the subnets within the NSI
def nsi_placement():
  # get the VIMs information registered to the SP
  vims_list = mapper.get_vims_info()
  LOG.info("NSI_MNGR: VIMs list information: " +str(vims_list))
  time.sleep(0.1)

  # validates if the incoming vim_list is empty (return 500) or not (follow)
  if not vims_list['vim_list']:
    return_msg = {}
    return_msg['error'] = "Not found any VIM information, register one to the SP."
    return return_msg, 500
  
  #nsi_placed = vims_list['vim_list'][0]['vim_uuid']
  for vim_item in vims_list['vim_list']:
    LOG.info("NSI_MNGR: looking for a vim: " +str(vim_item))
    time.sleep(0.1)
    if vim_item['type'] == "vm":
      LOG.info("NSI_MNGR: VIM FOUND -> " +str(vim_item['type']) + " with uuid ->  " +str(vim_item['vim_uuid']))
      time.sleep(0.1)
      nsi_placed = vim_item['vim_uuid']
      break

  LOG.info("NSI_MNGR: SELECTED VIM UUID: " +str(nsi_placed))
  time.sleep(0.1)
  
  return nsi_placed, 200

# Basic NSI structure
def add_basic_nsi_info(nst_json, nsi_json, main_datacenter):
  nsir_dict = {}
  nsir_dict['id'] = str(uuid.uuid4())
  nsir_dict['name'] = nsi_json['name']
  if nsi_json.get('description'):
    nsir_dict['description'] = nsi_json['description']
  else:
    nsir_dict['description'] = 'This NSr is based on ' + str(nsi_json['name'])
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
  nsir_dict['nsr-list'] = []
  nsir_dict['vldr-list'] = []

  return nsir_dict

# Adds the basic subnets information to the NSI record
def add_subnets(new_nsir, nst_json, request_nsi_json):
  nsr_list = []                         # empty list to add all the created slice-subnets
  serv_seq = 1                          # to put in order the services within a slice in the portal
  nsirs_ref_list = nsi_repo.get_all_saved_nsi()

  for subnet_item in nst_json["slice_ns_subnets"]:
    # Checks if there is a nsr record shared, if so copies the information.
    found_shared_nsr = False
    if subnet_item['is-shared']:
      LOG.info("NSI_MNGR: SHARED SUBNET")
      time.sleep(0.1)
      for nsir_ref_item in nsirs_ref_list:
        for nsir_subnet_ref_item in nsir_ref_item['nsr-list']:
          if nsir_subnet_ref_item['subnet-nsdId-ref'] == subnet_item['nsd-ref'] and nsir_subnet_ref_item['isshared']:
            LOG.info("NSI_MNGR: SHARED SUBNET - found a nsr reference")
            time.sleep(0.1)
            subnet_record = nsir_subnet_ref_item
            found_shared_nsr = True
            break
        if found_shared_nsr:
          break
      #TODO: what about the ingress and egress of a new slice having the shared NSR???
    
    # IF NSr is not shared or it is shared but not created
    if (subnet_item['is-shared'] == False or subnet_item['is-shared'] == True and found_shared_nsr == False):
      # Copying the basic subnet info from the NST to the NSI
      subnet_record = {}
      subnet_record['nsrName'] = new_nsir['name'] + "-" + subnet_item['id'] + "-" + str(serv_seq)
      subnet_record['nsrId'] = '00000000-0000-0000-0000-000000000000'
      subnet_record['vimAccountId'] = new_nsir['datacenter']
      subnet_record['working-status'] = 'NEW'    
      subnet_record['subnet-ref'] = subnet_item['id']
      subnet_record['subnet-nsdId-ref'] = subnet_item['nsd-ref']
      subnet_record['requestId'] = ''
      subnet_record['isshared'] = subnet_item['is-shared']
      
      # Checks if the subnet item has SLA, ingresses or egresses information
      if all(key in subnet_item for key in ('sla-name', 'sla-ref')):
        subnet_record['sla-name'] = subnet_item['sla-name']
        subnet_record['sla-ref'] = subnet_item['sla-ref']
      else:
        subnet_record['sla-name'] = "None"
        subnet_record['sla-ref'] = "None"
      if 'ingresses' in subnet_item:
        subnet_record['ingresses'] = subnet_item['ingresses']
      else:
        subnet_record['ingresses'] = []      
      if 'egresses' in subnet_item:
        subnet_record['egresses'] = subnet_item['egresses']
      else:
        subnet_record['egresses'] = []

      # Adding the instantiation parameters into the NSI subnet
      if 'instantiation_params' in request_nsi_json:
        instant_params = request_nsi_json['instantiation_params']
        for ip_item in instant_params:
          if ip_item['subnet_id'] == subnet_item['id']:
            # checking about SLA
            if all(key in instant_params for key in ('sla_id', 'sla_name')):
              subnet_record['sla-name'] = ip_item['sla_name']
              subnet_record['sla-ref'] = ip_item['sla_id']
            # checking about ingresses
            if 'ingresses' in instant_params:
              subnet_record['ingresses'] = ip_item['ingresses']
            # checking about egresses
            if 'egresses' in instant_params:
              subnet_record['egresses'] = ip_item['egresses']
      
      # adding the vld id where each subnet is connected to
      subnet_vld_list = []
      if (nst_json["slice_vld"]):
        for vld_item in nst_json["slice_vld"]:
          for nsd_cp_item in vld_item['nsd-connection-point-ref']:
            if subnet_item['id'] == nsd_cp_item['subnet-ref']:
              subnet_vld_item = {}
              subnet_vld_item['vld-ref'] = vld_item['id']
              subnet_vld_list.append(subnet_vld_item)
              break
      subnet_record['vld'] = subnet_vld_list

    nsr_list.append(subnet_record)
    serv_seq = serv_seq + 1
  
  new_nsir['nsr-list'] = nsr_list
  return new_nsir

# Sends requests to create vim networks and adds their information into the NSIr
def add_vlds(new_nsir, nst_json):
  vldr_list = []
  
  for vld_item in nst_json["slice_vld"]:
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
    
    # Defines the parameters 'ns-conn-point-ref' & 'access_net' of each slice_vld
    cp_refs_list = []
    for cp_ref_item in vld_item['nsd-connection-point-ref']:
      cp_dict = {}
      cp_dict[cp_ref_item['subnet-ref']] = cp_ref_item['nsd-cp-ref']
      cp_refs_list.append(cp_dict)
      
      for subn_item in nst_json["slice_ns_subnets"]:
        if subn_item['id'] == cp_ref_item['subnet-ref']:
          repo_item = mapper.get_nsd(subn_item['nsd-ref'])
          nsd_item = repo_item['nsd']
          for service_vl in nsd_item['virtual_links']:
            for service_cp_ref_item in service_vl['connection_points_reference']:
              if service_cp_ref_item == cp_ref_item['nsd-cp-ref']:
                if service_vl.get('access'):
                  vld_record['access_net'] = service_vl['access']
                else:
                  # To keep concordance with the old NSD, if it's not defined True
                  vld_record['access_net'] = True
    vld_record['ns-conn-point-ref'] = cp_refs_list
    vld_record['shared-nsrs-list'] = []
    vldr_list.append(vld_record)

  # SHARED functionality: looking for the alreade shared vld
  # modify the vldr only for those where an instantiated shared ns is conencted
  nsirs_ref_list = nsi_repo.get_all_saved_nsi()
  for nsr_item in new_nsir['nsr-list']:
    if nsr_item['isshared']:
      LOG.info("NSI_MNGR: SHARED VLDs")
      time.sleep(0.1)
      for nsir_ref_item in nsirs_ref_list:
        if (nsr_item['subnet-nsdId-ref'] == nsir_ref_item.get("subnet-nsdId-ref") and nsir_ref_item.get("isshared")):
          LOG.info("NSI_MNGR: SHARED VLD - found a nsir reference with a the same shared nsr.")
          time.sleep(0.1)
          for vld_nsr_item in nsr_item['vld']:
            for vldr_ref in nsirs_ref['vldr-list']:
              if vld_nsr_item['vld-ref'] == vldr_ref['id']:
                for current_vldr_item in vldr_list:
                  if current_vldr_item['id'] == vldr_ref['id']:
                    LOG.info("NSI_MNGR: SHARED VLD - current_vldr_item: " + str(current_vldr_item) + " & vldr_ref: " + str(vldr_ref))
                    time.sleep(0.1)
                    current_vldr_item['vim-net-id'] = vldr_ref['vim-net-id']
                    current_vldr_item['vimAccountId'] = vldr_ref['vimAccountId']
                    current_vldr_item['vld-status'] = 'ACTIVE'
                    current_vldr_item['type'] = vldr_ref['type']
                    current_vldr_item['shared-nsrs-list'] = vldr_ref['shared-nsrs-list']
  new_nsir['vldr-list'] = vldr_list
  return new_nsir

# Updates a NSI with the latest information coming from the MANO/GK
def update_instantiating_nsi(nsiId, request_json):
  LOG.info("NSI_MNGR: Updates the NSI with the latest incoming information.")
  time.sleep(0.1)
  jsonNSI = nsi_repo.get_saved_nsi(nsiId)
  if (jsonNSI):
    # starts the thread to update instantiation info within the services
    thread_update_slice_instantiation = update_slice_instantiation(nsiId, request_json)
    thread_update_slice_instantiation.start()

    return (jsonNSI, 200)
  else:
    return ('{"error":"There is no NSIR in the db."}', 500)

########################################## NSI TERMINATE SECTION #######################################
# 2 steps: terminate_nsi and update_terminating_nsi (with its internal functions)
# Does all the process to terminate the NSI
def terminate_nsi(nsiId, TerminOrder):
  LOG.info("NSI_MNGR: Terminates a NSI.")
  time.sleep(0.1)
  mutex_slice2db_access.acquire()
  try:
    terminate_nsi = nsi_repo.get_saved_nsi(nsiId)
    if (terminate_nsi):
      if terminate_nsi['nsi-status'] in ["INSTANTIATED", "ERROR"]:
        terminate_nsi["id"] = terminate_nsi["uuid"]
        del terminate_nsi["uuid"]

        # prepares time values to check if termination is done in the future
        if (TerminOrder['terminateTime'] == "0" or TerminOrder['terminateTime'] == 0):
          termin_time = 0
        else:
          termin_time = dateutil.parser.parse(TerminOrder['terminateTime'])
          instan_time = dateutil.parser.parse(terminate_nsi['instantiateTime'])

        # depending on the termin_time executes one action or another
        if termin_time == 0:
          terminate_nsi['terminateTime'] = str(datetime.datetime.now().isoformat())
          terminate_nsi['sliceCallback'] = TerminOrder['callback']
          terminate_nsi['nsi-status'] = "TERMINATING"

          for terminate_nsr_item in terminate_nsi['nsr-list']:
            # TODO SHARED: check if the item is shared and used in other nsirs to NOT change its status
            
            if (terminate_nsr_item['working-status'] != "ERROR"):
              terminate_nsr_item['working-status'] = "TERMINATING"

          updated_nsi = nsi_repo.update_nsi(terminate_nsi, nsiId)

          # starts the thread to terminate while sending back the response
          thread_ns_termination = thread_ns_terminate(terminate_nsi)
          thread_ns_termination.start()

          terminate_value = 200
          
        elif (instan_time < termin_time):                       # TODO: manage future termination orders
          terminate_nsi['terminateTime'] = str(termin_time)
          repo_responseStatus = nsi_repo.update_nsi(terminate_nsi, nsiId)

          terminate_value = 200
        else:
          inst_time = terminate_nsi['instantiateTime']
          terminate_nsi['errorLog'] = "Wrong value: 0 = instant termination, greater than " + inst_time + " future termination."
          terminate_value = 404
      else:
        terminate_nsi['errorLog'] = "This NSi is either terminated or being terminated."
        terminate_value = 404
    else:
      terminate_nsi['errorLog'] = "There is no NSIR in the db."
      terminate_value = 404
  
  finally:
    mutex_slice2db_access.release()
    return terminate_nsi, terminate_value

# Updates a NSI being terminated with the latest information coming from the MANO/GK.
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
    return_msg = {}
    return_msg['error'] = "There is no NSIR in the db."
    return (return_msg, 404)
  
# Deletes a NST kept in catalogues
def remove_nsi(nsiId):
  logging.info("NSI_MNGR: Delete NSI with id: " + str(nsiId))
  nsi_repo_response = nsi_repo.get_saved_nsi(nsiId)
  if (nsi_repo_response["nsi-status"] in ["TERMINATED", "ERROR"]):
    nsi_repo_response = nsi_repo.delete_nsi(nsiId)
    return (nsi_repo_response, 204)
  else:
    return_msg = {}
    return_msg['msg'] = "Either the NSI is not TERMINATED or it doesn't exist in the db, pelase check."
    return (return_msg, 403)

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
    return (return_msg, 404)

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