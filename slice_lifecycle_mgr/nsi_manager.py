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

import os, sys, logging, datetime, uuid, time, json, ast
import dateutil.parser
from threading import Thread, Lock

import objects.nsi_content as nsi
import slice2ns_mapper.mapper as mapper                             # sends requests to the GTK-SP
import slice_lifecycle_mgr.nsi_manager2repo as nsi_repo             # sends requests to the repositories
import slice_lifecycle_mgr.nst_manager2catalogue as nst_catalogue   # sends requests to the catalogues
from logger import TangoLogger

# INFORMATION
# mutex used to ensure one single access to ddbb (repositories) for the nsi records creation/update/removal
mutex_slice2db_access = Lock()

#Log definition to make the slice logs idetified among the other possible 5GTango components.
#LOG = TangoLogger.getLogger(__name__, log_level=logging.DEBUG, log_json=True)
#TangoLogger.getLogger("slicemngr:nsi_manager", logging.DEBUG, log_json=True)
#LOG.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("slicemngr:nsi_manager")
LOG.setLevel(logging.INFO)


################################## THREADs to manage services/slice requests #################################
# SENDS NETWORK SERVICE (NS) INSTANTIATION REQUESTS
## Objctive: reads subnets list in Network Slice Instance (NSI) and sends requests2GTK to instantiate them 
## Params: NSI - nsi created with the parameters given by the user and the NST saved in catalogues.
class thread_ns_instantiate(Thread):
  def __init__(self, NSI):
    Thread.__init__(self)
    self.NSI = NSI
  
  # Creates the json strcucture to request a NS instantiation.
  def send_instantiation_requests(self, nsr_item):
    LOG.info("NSI_MNGR: Instantiating Service: " + str(nsr_item['nsrName']))
    
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
      
      ## 'network_functions' object creation
      for nsr_place_item in nsr_item['nsr-placement']:
        net_funct = {}
        net_funct['vnf_id'] = nsr_place_item['nsd-comp-ref']
        net_funct['vim_id'] = nsr_place_item['vim-id']
        network_functions_list.append(net_funct)
      mapping['network_functions'] = network_functions_list
      
      ## 'virtual_links' object creation
      # for each nsr, checks its vlds and looks for its information in vldr-list
      for vld_nsr_item in nsr_item['vld']:
        inner_net_found = False
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
                      inner_net_found = True
                      break
                  if inner_net_found:
                    temp_vim_list = []
                    # as the link is found, creates vims list where to create network depending on the vnfs placement
                    for ns_cp_ref_item in nsd_vl_item['connection_points_reference']:
                      if ns_cp_ref_item.find(':') != -1:
                        vnf_id,cp_ref = ns_cp_ref_item.split(':')
                        for nsr_place_item in nsr_item['nsr-placement']:
                          if nsr_place_item['nsd-comp-ref'] == vnf_id and  nsr_place_item['vim-id'] not in temp_vim_list:
                            temp_vim_list.append(nsr_place_item['vim-id'])
                    break
              if inner_net_found:
                break
          
            #creates the objects to define how the slice-vld must be connected to the ns-vld.
            virt_link = {}
            virt_link['vl_id'] = vl_id
            virt_link['external_net'] = external_net

            for vim_id_item in temp_vim_list:
              virt_link['vim_id'] = vim_id_item
              virtual_links_list.append(virt_link)
      
      mapping['virtual_links'] = virtual_links_list
      
      #all the previous information into the mapping dict
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

    # calls the function towards the GTK
    instantiation_response = mapper.net_serv_instantiate(data)
    return instantiation_response

  # creates the json structure to request a WAN connection
  #INFORMATION: the multi-vim deployment is limited to share the vld within only 2 VIMs (improvement to be done)
  def configure_wim(self):
 
    # internal function to convert a string with format -> "key:value" into a dict -> "key":"value"
    def str_2_json(split_str):
      splitted_str = split_str[0].split(":")
      new_dict = {}
      new_dict['id'] = splitted_str[0]
      new_dict['cp'] = splitted_str[1]
      return new_dict

    # gets WIMS information list to check if the VIMs where to deploy the VNFs are registered within the WIM
    wims_list = mapper.get_wims_info()
    if wims_list[1] != 200:
      wims_list = json.loads(wims_list[0]['message'])
      self.NSI['errorLog'] = "WAN Enforcement: " + wims_list['error']
      self.NSI['nsi-status'] = "ERROR"
      LOG.info("NSI_MNGR: WAN FAILED: " + str(wims_list['error']))
      time.sleep(0.1)

      return self.NSI, 501

    LOG.info("NSI_MNGR: WAN looking for VLD")
    time.sleep(0.1)
    # loops the slice-vld to find out which one is in two different VIMs
    for vldr_item in self.NSI['vldr-list']:
      # only those not management vld
      if (vldr_item.get('mgmt-network') == None or vldr_item['mgmt-network'] == False):
        
        # nst IF/ELSE simply checks if the checks if the vldr_item needs WIM enforcement
        vld_wim_found = False
        if len(vldr_item['vim-net-stack']) > 1:
          # multiple stacks with different vims
          vld_wim_found = True
        else:
          # one stack with many vims
          vim_net_item = vldr_item['vim-net-stack'][0]
          if len(vim_net_item['vimAccountId']) > 1:
            vld_wim_found = True

        # if true, this VLD needs WAN enforcement
        if vld_wim_found:
          LOG.info("NSI_MNGR: FOUND VLD THAT NEEDS WAN")
          time.sleep(0.1)
          wim_conn_points_list = []
          info_found = False
          
          # from the SLICE-CP looks for the IP associated to the VDU linked to that CP.
          for ns_cp_item in vldr_item['ns-conn-point-ref']:
            for nsr_item in self.NSI['nsr-list']:
              # compares with the only key within the dict
              found_vnfd = False
        
              if nsr_item['subnet-ref'] in ns_cp_item.keys():
                # get the nsr information in order to go into the next level (VNFs info)
                nsr_json = mapper.get_nsr(nsr_item['nsrId'])
                
                for nsr_vl_item in nsr_json['virtual_links']:
                  # checks if the value exists within the nsr cp-reference
                  if ns_cp_item[nsr_item['subnet-ref']] in nsr_vl_item['connection_points_reference']:
                    found_ns_cp = nsr_vl_item['connection_points_reference']
                    found_ns_cp.remove(ns_cp_item[nsr_item['subnet-ref']])
                    found_ns_cp = str_2_json(found_ns_cp)
                
                    # if the value exist, requests the NSD to find out the VNFD name which the vnfr is based on
                    nsd_json = mapper.get_nsd(nsr_json['descriptor_reference'])
                    for nsd_nf_item in nsd_json['nsd']['network_functions']:
                      if nsd_nf_item['vnf_id'] == found_ns_cp['id']:
                        # the right VNF name is found
                        found_vnfd_name = nsd_nf_item['vnf_name']
                        found_vnfd = True
                        break
                  if found_vnfd:
                    break

              if found_vnfd:
                # among all the VNFRs within the NSR, looks fo rthe one based on the VNF name found previously
                for nsr_nf_item in nsr_json['network_functions']:
                  found_vnfr = False
                  vnfr_json = mapper.get_vnfr(nsr_nf_item['vnfr_id'])
                  if vnfr_json['name'] == found_vnfd_name:
                    for vnfr_vl_item in vnfr_json['virtual_links']:
                      # looks for the VLD connected to the selected VNFR external CP
                      if found_ns_cp['cp'] in vnfr_vl_item['connection_points_reference']:
                        found_vnf_cp = vnfr_vl_item['connection_points_reference']
                        found_vnf_cp.remove(found_ns_cp['cp'])
                        found_vnf_cp = str_2_json(found_vnf_cp)
                        break

                    # looks for the VDU that is connected to the CP pointing out of the slice
                    for vnfr_vdu_item in vnfr_json['virtual_deployment_units']:
                      if vnfr_vdu_item['id'] == found_vnf_cp['id']:
                        for vnfc_ins_item in vnfr_vdu_item['vnfc_instance']:
                          for vnfc_ins_cp_item in vnfc_ins_item['connection_points']:
                            if vnfc_ins_cp_item['id'] == found_vnf_cp['cp']:
                              # VDU found, takins its information for the WIM request
                              wim_dict = {}
                              wim_dict['location'] = vnfc_ins_item['vim_id']
                              wim_dict['nap'] = vnfc_ins_cp_item['interface']['address']
                              wim_conn_points_list.append(wim_dict)
                              found_vnfr = True
                              break
                          if found_vnfr:
                            break
                      if found_vnfr:
                        break
                  if found_vnfr:
                    break
          
          #TODO: Improve the following code as it assumes that each VLD has ONLY two nsrs connected [0] & [1]
          # JSON creation and WAN request
          if wim_conn_points_list:
            LOG.info("NSI_MNGR: inside win_conn_points_list")
            time.sleep(0.1)
            wim_uuid = None
            # validates if the two VIMs are registered within the same WIM
            for wim_item in wims_list[0]['wim_list']:
              found_wim = True
              # if any of the two vim_uuids is not in the wim_attached_vims_list, check the next wim
              for wim_cp_item in wim_conn_points_list:
                if wim_cp_item['location'] not in wim_item['attached_vims']:
                  found_wim = False
                  break
              
              if found_wim:
                wim_uuid = wim_item['uuid']
                break
          
            # creates the json to request the WIM connection
            wim_dict = {}
            wim_dict['instance_uuid'] = vldr_item['vim-net-id']   # GTK translates it to service_instance_id for the IA.
            wim_dict['wim_uuid'] = wim_uuid
            wim_dict['vl_id'] = vldr_item['id']
            wim_dict['ingress'] = wim_conn_points_list[0]
            wim_dict['egress'] = wim_conn_points_list[1]
            wim_dict['bidirectional'] = True

            # checks if there's already a WIM connection with the same ingress/egress IP @s. If so, no need to create.
            create_wim = True
            if self.NSI['_wim-connections']:
              for wim_connection_item in self.NSI['_wim-connections']:
                if wim_connection_item['vl_id'] == wim_dict['vl_id']:

                  ref_ingress = wim_connection_item['ingress']['nap']
                  ref_egress = wim_connection_item['egress']['nap']
                  new_ingress = wim_dict['ingress']['nap']
                  new_egress = wim_dict['egress']['nap']
                  
                  if new_ingress == ref_ingress and new_egress == ref_egress:
                    LOG.info("NSI_MNGR: WIM already exists with this ingress/egress IP @s")
                    create_wim = False
                  elif new_ingress == ref_egress and new_egress == ref_ingress:
                    LOG.info("NSI_MNGR: WIM already exists with this ingress/egress IP @s")
                    create_wim = False
                  else:
                    continue
                  
                if not create_wim:
                  break

            # if there's no equal existing WIM connection (create_wim = True), enters and requests it.
            if create_wim:
              LOG.info("NSI_MNGR: JSON to request WIM configuration: " + str(wim_dict))
              wim_response = mapper.create_wim_network(wim_dict)
              if wim_response['status'] == 'COMPLETED':
                self.NSI['_wim-connections'].append(wim_dict)
                #return self.NSI, 200
              else:
                LOG.info("NSI_MNGR: WAN Enforcement: " + str(wim_response) + " NOT created.")
                wim_response = json.loads(wim_response['message'])
                self.NSI['errorLog'] = "WAN Enforcement: " + wim_response['error']
                self.NSI['nsi-status'] = 'ERROR'
                return self.NSI, 501
          else:
            return self.NSI, 501

    # this return only happens if the WIM connection already exists and connects two shared nsrs
    return self.NSI, 200

  # requests to remove the networks of a failed nsi
  def undo_slice_vlds(self):
    self.NSI['nsi-status'] == "TERMINATING"
    #checks if the vldr can be removed (if they are not shared or shared with terminated nsrs)
    for vldr_item in self.NSI['vldr-list']:
      if vldr_item.get('shared-nsrs-list'):
        for shared_nsrs_item in vldr_item['shared-nsrs-list']:
          remove_vldr_item = True
          # if the nsr is still with status ['NEW', 'INSTANTIATING', 'INSTANTIATED', 'READY'], another nsi uses it
          for nsrs_item in self.NSI['nsr-list']:
            if (shared_nsrs_item == nsrs_item['nsrId'] and nsrs_item['working-status'] in ['NEW', 'INSTANTIATING', 'INSTANTIATED', 'READY']):
              remove_vldr_item = False
              break
          if remove_vldr_item == False:
            break
      else:
        remove_vldr_item = True
      
      if remove_vldr_item:
        # remove the created networks in order to avoid having unused resources
        for vldr_item in self.NSI['vldr-list']:
          if vldr_item['vld-status'] == 'ACTIVE':
            virtual_links = []
            virtual_links_item = {}
            virtual_links_item['id'] = vldr_item['vim-net-id']
            virtual_links.append(virtual_links_item)

            for vim_net_stack_item in vldr_item['vim-net-stack']:
              vim_list = []
              network_data = {}
              network_data['instance_id'] = vim_net_stack_item['id']
              for vim_item in vim_net_stack_item['vimAccountId']:
                vim_list_item = {}
                vim_list_item['uuid'] = vim_item['vim-id']
                vim_list_item['virtual_links'] = virtual_links
                vim_list.append(vim_list_item)

              network_data['vim_list'] = vim_list

              LOG.info("NSI_MNGR: network_data: " + str(network_data))
              networks_response = mapper.delete_vim_network(network_data)
            
              if networks_response['status'] == 'COMPLETED':
                vldr_item['vld-status'] = 'INACTIVE'
              else:
                vldr_item['vld-status'] = 'ERROR'
                error_dict = json.loads(networks_response['message'])
                self.NSI['errorLog'] = error_dict['error']

  # requests to terminate those instantiated nsr of a failed nsi
  def undo_nsrs(self, nsrs_2_terminate):
    for nsrid_item in nsrs_2_terminate:
      # requests to terminate a NSr
      data = {}
      data["instance_uuid"] = str(nsrid_item)
      data["request_type"] = "TERMINATE_SERVICE"
      data['callback'] = "http://tng-slice-mngr:5998/api/nsilcm/v1/nsi/"+str(self.NSI['id'])+"/terminate-change"

      # calls the function towards the GTK
      termination_response = mapper.net_serv_terminate(data)

      for nsr_item in self.NSI['nsr-list']:
        if nsrid_item == nsr_item['nsrId']:
          nsr_item['working-status'] == 'TERMINATING'
          nsr_item['requestId'] = termination_response['id']
          break

    return self.NSI, 200

  # TODO: Improve the code in order to avoid duplicated code:
  # .... The code within the next funcion is also inside the terminate_nsi(nsiId, TerminOrder) function, this should 
  # .... be avoid and only have one time the code.
  # Looks for any "INSTANTIATING/INSTANTIATED" nsi sharing a nsr with the current terminating nsi
  def find_shared_nsr(self):
    ## CREATES A LIST OF NSRs TO TERMINATE CHECKING IF EACH NSR IS SHARED WITH OTHER NSIRs
    # creates a nsirs list without the current one
    nsirs_ref_list = nsi_repo.get_all_saved_nsi()
    nsirs_list_no_current = []
    for nsir_item in nsirs_ref_list:
      if nsir_item['uuid'] != self.NSI['id']:
        nsirs_list_no_current.append(nsir_item)
    
    # checks if each NSR of the current nsir can be terminated depending if it is shared by other nsirs
    termin_nsrids_list = []
    for termin_nsr_item in self.NSI['nsr-list']:
      # if there are other nsirs follow, if not terminate nsr
      if nsirs_list_no_current:
        # creates a list of nsirs with only those having the current nsr
        nsirs_list_with_nsr = []
        for nsir_ref_item in nsirs_list_no_current:
          for nsr_ref_item in nsir_ref_item['nsr-list']:
            if nsr_ref_item['nsrId'] == termin_nsr_item['nsrId']:
              nsirs_list_with_nsr.append(nsir_ref_item)

        if nsirs_list_with_nsr:
          # from the previous reduced list, creates a list of nsirs with status [INSTANTIATED, INSTANTIATING, READY]
          instantiated_nsirs_list_with_nsr = []
          for nsir_ref_item in nsirs_list_with_nsr:
            if nsir_ref_item['nsi-status'] in ['INSTANTIATED', 'INSTANTIATING', 'READY']:
              instantiated_nsirs_list_with_nsr.append(nsir_ref_item)

          if instantiated_nsirs_list_with_nsr:
            nsr_to_terminate = False
          else:
            nsr_to_terminate = True
        else:
          nsr_to_terminate = True
      else:
        nsr_to_terminate = True
      
      # if true, there's not other nsirs sharing the current nsr and so, it can be terminated.
      if nsr_to_terminate:
        termin_nsr_item['working-status'] == 'TERMINATING'
        termin_nsrids_list.append(termin_nsr_item['nsrId'])
    
    return termin_nsrids_list, 200

  # once all the instantiation is done, calls back the GTK to notify the final result.
  def update_nsi_notify_instantiate(self):
    mutex_slice2db_access.acquire()
    try:
      jsonNSI = self.NSI

      # updates the slice information before notifying the GTK
      if (jsonNSI['nsi-status'] == "INSTANTIATING"):
        jsonNSI['nsi-status'] = "INSTANTIATED"

        # validates if any service has error status to apply it to the slice status
        for service_item in jsonNSI['nsr-list']:
          if (service_item['working-status'] == "ERROR"):
            service_item['working-status'] = 'ERROR'
            jsonNSI['nsi-status'] = "ERROR"

        # updates NetSlice template usageState
        if (jsonNSI['nsi-status'] == "INSTANTIATED"):
          nst_descriptor = nst_catalogue.get_saved_nst(jsonNSI['nst-ref'])
          if (nst_descriptor['nstd'].get('usageState') == "NOT_IN_USE"):
            nstParameter2update = "usageState=IN_USE"
            updatedNST_jsonresponse = nst_catalogue.update_nst(nstParameter2update, jsonNSI['nst-ref'])
      
      elif (jsonNSI['nsi-status'] == "TERMINATING"):
        jsonNSI['nsi-status'] = "TERMINATED"

        # updates NetSlice template usageState if no other nsi is instantiated/ready
        nsis_list = nsi_repo.get_all_saved_nsi()
        all_nsis_terminated = True
        for nsis_item in nsis_list:
          if (nsis_item['nst-ref'] == jsonNSI['nst-ref'] and nsis_item['nsi-status'] in ["INSTANTIATED", "INSTANTIATING", "READY"]):
              all_nsis_terminated = False
              break
        
        if (all_nsis_terminated):
          nst_descriptor = nst_catalogue.get_saved_nst(jsonNSI['nst-ref'])
          nst_json = nst_descriptor['nstd']
          if (nst_json['usageState'] == "IN_USE"):
            nstParameter2update = "usageState=NOT_IN_USE"
            updatedNST_jsonresponse = nst_catalogue.update_nst(nstParameter2update, jsonNSI['nst-ref'])

      else:
        # errors are managed in the main thread function (run)
        jsonNSI['nsi-status'] = 'ERROR'
      
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
      json_slice_info['name'] = jsonNSI['name']
      json_slice_info['instance_uuid'] = jsonNSI['id']

      thread_response = mapper.sliceUpdated(slice_callback, json_slice_info)
      LOG.info("NSI_MNGR: THREAD FINISHED, GTK notified with status: " +str(thread_response[1]))
  
  # basic function that manages the whole instantiation.
  def run(self):

    # set to true in order to instantiates NSs in case there are no slice_vld to create
    network_ready = True

    # acquires mutex to have unique access to the nsi (repositories)
    mutex_slice2db_access.acquire()
    try:
      # enters only if there are vld/networks to create
      if self.NSI.get('vldr-list'):
        LOG.info("NSI_MNGR: Creating Network Slice VLDs (VIM Networks).")
        # creates each one of the vlds defined within the nsir
        for vldr_item in self.NSI['vldr-list']:
          # if ACTIVE, the vld is shared and there's no need to create it again
          if vldr_item['vld-status'] == "INACTIVE" or len(vldr_item['vim-net-stack']) > 1:
            # creates the json object with the information for the request payload
            virtual_links = []
            virtual_links_item = {}
            virtual_links_item['id'] = vldr_item['vim-net-id']
            virtual_links_item['access'] = vldr_item['access_net']
            virtual_links.append(virtual_links_item)
            #TODO FUTURE: there are other parameters that could be added (i.e. minimum_BW, qos_requirements...)

            vim_list = []
            for vim_net_stack_item in vldr_item['vim-net-stack']:
              for vim_item in vim_net_stack_item['vimAccountId']:
                if not vim_item['net-created']:
                  vim_list_item = {}
                  vim_list_item['uuid'] = vim_item['vim-id']
                  vim_list_item['virtual_links'] = virtual_links
                  vim_list.append(vim_list_item)
              
              if vim_list:
                network_data = {}
                network_data['instance_id'] = vim_net_stack_item['id']
                network_data['vim_list'] = vim_list

                # calls the function towards the GTK
                networks_response = mapper.create_vim_network(network_data)

                # checks that all the networks are created. otherwise, (network_ready = False) services are not requested
                if networks_response['status'] == 'COMPLETED':
                  LOG.info("NSI_MNGR: Network Slice VLD: " + str(networks_response) + " created.")
                  vldr_item['vld-status'] = 'ACTIVE'

                  for vim_item in vim_net_stack_item['vimAccountId']:
                    if vim_item['net-created'] == False:
                      vim_item['net-created'] = True

                else:
                  LOG.info("NSI_MNGR: Network Slice VLD: " + str(networks_response) + " NOT created.")
                  vldr_item['vld-status'] = 'ERROR'
                  self.NSI['errorLog'] = networks_response['error']
                  network_ready = False
              
              if not network_ready:
                break
          if not network_ready:
            break

      # if TRUE = instantiates the services, otherwise REMOVES created networks
      if network_ready:
        LOG.info("NSI_MNGR: Instantiating Network Service Instances.")
        time.sleep(0.1)
        for nsr_item in self.NSI['nsr-list']:
          if (nsr_item['isshared'] == False or nsr_item['isshared'] and nsr_item['working-status'] == "NEW"):
            instantiation_resp = self.send_instantiation_requests(nsr_item)
            if instantiation_resp[1] == 201:
              nsr_item['working-status'] == 'INSTANTIATING'
              nsr_item['requestId'] = instantiation_resp[0]['id']
            else:
              nsr_item['working-status'] == 'ERROR'
              self.NSI['errorLog'] = 'ERROR when instantiating ' + str(nsr_item['nsrName'])
      else:
        self.undo_slice_vlds()
        for nss_item in self.NSI['nsr-list']:
          nss_item['working-status'] = 'NOT_INSTANTIATED'
        
      # sends the updated NetSlice instance to the repositories
      repo_responseStatus = nsi_repo.update_nsi(self.NSI, self.NSI['id'])
    finally: 
      # releases mutex for any other thread to acquire it
      mutex_slice2db_access.release()
      
      # if all networks are well created, enters into the NSs instantiation step
      if network_ready:
        LOG.info("NSI_MNGR: PROCESSING all Network Service Instances for slice: " + str(self.NSI['id']))
        # Waits until all the NSs are instantiated/ready or error
        deployment_timeout = 900   # 15min   #TODO: mmodify for the reviews
        while deployment_timeout > 0:
          # Check ns instantiation status
          nsrs_instantiated = True
          jsonNSI = nsi_repo.get_saved_nsi(self.NSI['id'])
          for nsr_item in jsonNSI['nsr-list']:
            if nsr_item['working-status'] not in ["INSTANTIATED", "ERROR", "READY"]:
              nsrs_instantiated = False
              break
          
          # if all services are instantiated, break the while and proceed with the last steps
          if nsrs_instantiated:
            LOG.info("NSI_MNGR: ALL Network Service Instantiations requests processed for slice: " + str(self.NSI['id']))
            break
      
          time.sleep(15)
          deployment_timeout -= 15
        
        # adapting the record from tng-repos, to the tng-slice-mngr record.
        jsonNSI["id"] = jsonNSI["uuid"]
        del jsonNSI["uuid"]
        self.NSI = jsonNSI
        nsr_error = False
        wim_ready = True
        
        # check if there's any NSR with error or still instantiating due to deployment time out.
        for nsr_item in self.NSI['nsr-list']:
          if nsr_item['working-status'] in ["ERROR", "INSTANTIATING"]:
            nsr_error = True
            break

        # if any nsr failed, follows the process. if a nsr failed, undoes all nsr and vldr instantiated.
        if nsr_error == False:
          # if the slice is distributed in many VIMs, it starts the configuration of the WAN link
          if len(jsonNSI['datacenter']) > 1:
            LOG.info("NSI_MNGR: Configuring WAN Connection for multi-vim instantiation.")
            # WAN ENFORCEMENT FOR MULTI-VIM DEPLOYMENTS
            wim_configured = self.configure_wim()
            if wim_configured[1] != 200:
              wim_ready = False

        # FUTURE TODO: ensure this "undo" process is well done.         
        # undoes everything done until this moment (nsrs, and vlds)
        if nsr_error == True or wim_ready == False:
          LOG.info("NSI_MNGR: Undoing all the created objects (nsrs and vlds")
          # acquires mutex to have unique access to the nsi (repositories)
          mutex_slice2db_access.acquire()
          
          # TODO: improve this section as it only sends the terminate request and considers...
          # ... the nsr already as terminate withouth waiting the confirmation from GTK.
          check_shared = self.find_shared_nsr()
          
          if check_shared[0]:
            # TERMINATES NSRS within the given list.
            self.undo_nsrs(check_shared[0])
            
            # sends the updated NetSlice instance to the repositories
            repo_responseStatus = nsi_repo.update_nsi(self.NSI, self.NSI['id'])

            # releases mutex for any other thread to acquire it
            mutex_slice2db_access.release()
            
            # waits until all nsrs are either ERROR/TERMINATED or INSTANTIATED (if shared)
            nsrs_terminated = False
            while nsrs_terminated == False:
              nsrs_terminated = True
              jsonNSI = nsi_repo.get_saved_nsi(self.NSI['id'])
              for nsr_item in jsonNSI['nsr-list']:
                if nsr_item['working-status'] == 'TERMINATING':
                  nsrs_terminated = False
                  time.sleep(15)
                  break
            
            # TERMINATES VLDRS, if they are not shared
            self.undo_slice_vlds()
          else:
            # releases mutex for any other thread to acquire it
            mutex_slice2db_access.release()
      
      else:
        self.undo_slice_vlds()
        self.NSI['nsi-status'] = 'ERROR'
      
      # Notifies the GTK about the NetSlice process is done (either completed or error).
      LOG.info("NSI_MNGR: Updating network slice record and notifying instantiation to GTK")
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
    # acquires mutex to have unique access to the nsi (repositories)
    mutex_slice2db_access.acquire()
    try:
      LOG.info("NSI_MNGR: Updating NSI instantiation: " + str(self.nsiId))
      time.sleep(0.1)
      jsonNSI = nsi_repo.get_saved_nsi(self.nsiId)
      jsonNSI["id"] = jsonNSI["uuid"]
      del jsonNSI["uuid"]

      serviceInstance = {}
      # looks all the already added services and updates the right
      for service_item in jsonNSI['nsr-list']:
        # if the current request already exists, update it.
        if (service_item['nsrName'] == self.request_json['name'] and service_item['requestId'] == self.request_json['id']):
          
          # check if there's an id of the instantiation within the VIM
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
          elif (self.request_json['status'] == "ERROR"):
            service_item['working-status'] = "ERROR"
            jsonNSI['errorLog'] = self.request_json['error']
          else:
            service_item['working-status'] = self.request_json['status']
          break;

      # sends updated nsi to the DDBB (tng-repositories)
      jsonNSI['updateTime'] = str(datetime.datetime.now().isoformat())
      repo_responseStatus = nsi_repo.update_nsi(jsonNSI, self.nsiId)
    
    finally:
      # releases mutex for any other thread to acquire it
      mutex_slice2db_access.release()

# SENDS NETWORK SERVICE (NS) TERMINATION REQUESTS
## Objctive: gets the specific nsi record from db and sends the ns termination requests 2 GTK
## Params: nsiId (uuid within the incoming request URL)
class thread_ns_terminate(Thread):
  def __init__(self, NSI, termin_nsrids_list):
    Thread.__init__(self)
    self.NSI = NSI
    self.termin_nsrids_list = termin_nsrids_list
  
  def send_termination_requests(self, nsr_item):
    LOG.info("NSI_MNGR: Terminating Service: " + str(nsr_item))
    time.sleep(0.1)

    data = {}
    data["instance_uuid"] = str(nsr_item)
    data["request_type"] = "TERMINATE_SERVICE"
    data['callback'] = "http://tng-slice-mngr:5998/api/nsilcm/v1/nsi/"+str(self.NSI['id'])+"/terminate-change"

    # calls the function towards the GTK
    termination_response = mapper.net_serv_terminate(data)

    return termination_response, 201
  
  def update_nsi_notify_terminate(self):
    mutex_slice2db_access.acquire()
    try:
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
      json_slice_info['name'] = jsonNSI['name']
      json_slice_info['instance_uuid'] = jsonNSI['id']

      thread_response = mapper.sliceUpdated(slice_callback, json_slice_info)
      LOG.info("NSI_MNGR_Notify: THREAD FINISHED, GTK notified with status: " +str(thread_response[1]))

  def run(self):
    # acquires mutex to have unique access to the nsi (rpositories)
    mutex_slice2db_access.acquire()
    
    # remove WAN connections if there are more than one element in nsir['datacenter']
    if self.NSI['_wim-connections']:
      for wan_item in self.NSI['_wim-connections']:

        LOG.info("NSI_MNGR: Removing WAN conenction for the VLD:.")
        # creates the json to request the WIM connection
        wim_dict = {}
        wim_dict['instance_uuid'] = wan_item['instance_uuid'] # GTK translates it to service_instance_id for the IA.
        wim_dict['wim_uuid'] = wan_item['wim_uuid']
        wim_dict['vl_id'] = wan_item['vl_id']

        LOG.info("NSI_MNGR: JSON to remove WIM conection:" + str(wim_dict))
        time.sleep(0.1)
        wim_response = mapper.delete_wim_network(wim_dict)
        if wim_response['status'] != 'COMPLETED':
          LOG.info("NSI_MNGR: WAN Enforcement: " + str(wim_response) + " NOT removed.")
          self.NSI['errorLog'] = "WAN Enforcement Removal Error."
          self.NSI['nsi-status'] = 'ERROR'
          return self.NSI, 501

    # sends each of the termination requests
    LOG.info("NSI_MNGR: Terminating Network Service Instantiations.")

    #TODO: missing to take into account the option of an empty list (all nsrs are shared and used), then just update the general nsirs info.
    for nsrid_item in self.termin_nsrids_list:
      # requests to terminate a NSr
      termination_resp = self.send_termination_requests(nsrid_item)
      for nsr_item in self.NSI['nsr-list']:
        if nsrid_item == nsr_item['nsrId']:
          if termination_resp[1] == 201:
            nsr_item['working-status'] == 'TERMINATING'
            nsr_item['requestId'] = termination_resp[0]['id']
          else:
            nsr_item['working-status'] == 'ERROR'
            self.NSI['errorLog'] = 'ERROR when terminating ' + str(nsr_item['nsrName'])
          break
    
    # sends the updated NetSlice instance to the repositories
    repo_responseStatus = nsi_repo.update_nsi(self.NSI, self.NSI['id'])

    # releases mutex for any other thread to acquire it
    mutex_slice2db_access.release()

    # Waits until all the NSs are terminated/ready or error
    # deployment_timeout = 2 * 3600   # Two hours
    deployment_timeout = 900         # 15 minutes  #TODO: mmodify for the reviews
    while deployment_timeout > 0:
      # Check ns instantiation status
      nsi_terminated = True
      self.NSI = nsi_repo.get_saved_nsi(self.NSI['id'])
      #due to a missmatch with repositories
      self.NSI["id"] = self.NSI["uuid"]
      del self.NSI["uuid"]
      
      for nsr_item in self.NSI['nsr-list']:
        if nsr_item['isshared']:
          if nsr_item['working-status'] not in ["TERMINATED", "INSTANTIATED", "ERROR", "READY"]:
            nsi_terminated = False
        else:
          if nsr_item['working-status'] not in ["TERMINATED", "ERROR", "READY"]:
            nsi_terminated = False
        if not nsi_terminated:
          break
      
      # if all services are instantiated or error, break the while loop to notify the GTK
      if nsi_terminated:
        LOG.info("All Network Service Terminations requests processed!")
        time.sleep(0.1)
        break
  
      time.sleep(15)
      deployment_timeout -= 15
    
    # enters only if there are vld/networks to terminate
    if self.NSI.get('vldr-list'):
      LOG.info("NSI_MNGR: Removing Network Slice networks.")
      # acquires mutex to have unique access to the nsi (repositories)
      mutex_slice2db_access.acquire()
      
      #checks if the vldr can be removed (if they are not shared or shared with terminated nsrs)
      for vldr_item in self.NSI['vldr-list']:
        if vldr_item.get('shared-nsrs-list'):
          for shared_nsrs_item in vldr_item['shared-nsrs-list']:
            remove_vldr_item = True
            # if the nsr is still with status ['NEW', 'INSTANTIATING', 'INSTANTIATED', 'READY'], another nsi uses it
            for nsrs_item in self.NSI['nsr-list']:
              if (shared_nsrs_item == nsrs_item['nsrId'] and nsrs_item['working-status'] in ['NEW', 'INSTANTIATING', 'INSTANTIATED', 'READY']):
                remove_vldr_item = False
                break
            if remove_vldr_item == False:
              break
        else:
          remove_vldr_item = True
        
        if remove_vldr_item:
          virtual_links = []
          virtual_links_item = {}
          virtual_links_item['id'] = vldr_item['vim-net-id']
          virtual_links.append(virtual_links_item)

          vim_list = []
          # to remove the net if it si placed in multiple VIMs
          
          for vim_net_stack_item in vldr_item['vim-net-stack']:
            for vimAccountID_item in vim_net_stack_item['vimAccountId']:
              vim_list_item = {}
              vim_list_item['uuid'] = vimAccountID_item['vim-id']
              vim_list_item['virtual_links'] = virtual_links
              vim_list.append(vim_list_item)

            network_data = {}
            network_data['instance_id'] = vim_net_stack_item['id']
            network_data['vim_list'] = vim_list

            # calls the function towards the GTK
            networks_response = mapper.delete_vim_network(network_data)

            # checks that all the networks are terminated
            if networks_response['status'] in ['COMPLETED']:
              vldr_item['vld-status'] = "INACTIVE"
            else:
              vldr_item['vld-status'] = "ERROR"
              self.NSI['nsi-status'] = "ERROR"
              self.NSI['errorLog'] = networks_response['error']

      # sends the updated NetSlice instance to the repositories
      repo_responseStatus = nsi_repo.update_nsi(self.NSI, self.NSI['id'])

      # releases mutex for any other thread to acquire it
      mutex_slice2db_access.release()

    # Notifies the GTK that the Network Slice termination process is done (either complete or error)
    LOG.info("NSI_MNGR: Updating and notifying terminate to GTK")
    time.sleep(0.1)
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
      LOG.info("NSI_MNGR: Updating NSI Termination")
      time.sleep(0.1)
      jsonNSI = nsi_repo.get_saved_nsi(self.nsiId)
      jsonNSI["id"] = jsonNSI["uuid"]
      del jsonNSI["uuid"]

      # looks for the right service within the slice and updates it with the new data
      for service_item in jsonNSI['nsr-list']:
        if (service_item['nsrId'] == self.request_json['instance_uuid']):
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

  # check if exists another nsir with the same name, based on the same NSTd and not instantiated
  nsirepo_jsonresponse = nsi_repo.get_all_saved_nsi()
  if nsirepo_jsonresponse:
    for nsir_item in nsirepo_jsonresponse:
      if (nsir_item["name"] == nsi_json['name'] and \
          nsir_item["nst-ref"] == nstId and \
          nsir_item["nst-version"] == nst_json['version'] and \
          nsir_item["vendor"] == nst_json['vendor'] and \
          nsir_item["nsi-status"] not in ["TERMINATED", "TERMINATING", "ERROR"] ):
        return_msg = {}
        return_msg['error'] = "There is already an INSTANTIATED slice with this name and based on the selected NSTd (id/name/vendor/version)."
        return (return_msg, 400)
   
  # creates NSI with the received information
  LOG.info("NSI_MNGR: Creating NSI record basic structure.")
  new_nsir = add_basic_nsi_info(nst_json, nsi_json)
  
  # adds the NetServices (subnets) information within the NSI record
  LOG.info("NSI_MNGR:  Adding subnets into the NSI structure.")
  new_nsir = add_subnets(new_nsir, nst_json, nsi_json)

  #TODO: validate if all NSD composing the slice axist in the database.
  
  # adds the VLD information within the NSI record
  if nst_json.get('slice_vld'):
    LOG.info("NSI_MNGR:  Adding vlds into the NSI structure.")
    new_nsir = add_vlds(new_nsir, nst_json)
  
  # Network Slice Placement
  LOG.info("NSI_MNGR:  Placement of the Network Service Instantiations.")
  new_nsir = nsi_placement(new_nsir)

  if new_nsir[1] != 200:
    LOG.info("NSI_MNGR: Error returning saved nsir.")
    return (new_nsir[0], new_nsir[1])
  
  # saving the NSI into the repositories
  nsirepo_jsonresponse = nsi_repo.safe_nsi(new_nsir[0])
  
  if nsirepo_jsonresponse[1] == 200:
    # starts the thread to instantiate while sending back the response
    thread_ns_instantiation = thread_ns_instantiate(new_nsir[0])
    thread_ns_instantiation.start()
  else:
    error_msg = nsirepo_jsonresponse[0]
    new_nsir['errorLog'] = error_msg['message']
    return (new_nsir, 400)

  return nsirepo_jsonresponse
  
# Basic NSI structure
def add_basic_nsi_info(nst_json, nsi_json):
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
  nsir_dict['datacenter'] = []
  nsir_dict['instantiateTime'] = str(datetime.datetime.now().isoformat())
  nsir_dict['terminateTime'] = ''
  nsir_dict['scaleTime'] = ''
  nsir_dict['updateTime'] = ''
  nsir_dict['sliceCallback'] = nsi_json['callback']  #URL used to call back the GK when the slice instance is READY/ERROR
  nsir_dict['nsr-list'] = []
  nsir_dict['vldr-list'] = []
  nsir_dict['_wim-connections']=[]

  return nsir_dict

# Adds the basic subnets information to the NSI record
def add_subnets(new_nsir, nst_json, request_nsi_json):
  nsr_list = []                         # empty list to add all the created slice-subnets
  serv_seq = 1                          # to put in order the services within a slice in the portal
  nsirs_ref_list = nsi_repo.get_all_saved_nsi()
  for subnet_item in nst_json["slice_ns_subnets"]:
    # Checks if there is already a shared nsr and copies its information
    found_shared_nsr = False
    if subnet_item['is-shared']:
      if nsirs_ref_list:
        for nsir_ref_item in nsirs_ref_list:
          if nsir_ref_item['nsi-status'] in ['NEW', 'INSTANTIATING', 'INSTANTIATED', 'READY']:
            for nsir_subnet_ref_item in nsir_ref_item['nsr-list']:
              if nsir_subnet_ref_item['subnet-nsdId-ref'] == subnet_item['nsd-ref'] and nsir_subnet_ref_item['isshared']:
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
      subnet_record['nsr-placement'] = []
      subnet_record['working-status'] = 'NEW'    
      subnet_record['subnet-ref'] = subnet_item['id']
      subnet_record['subnet-nsdId-ref'] = subnet_item['nsd-ref']
      subnet_record['requestId'] = '00000000-0000-0000-0000-000000000000'
      subnet_record['isshared'] = subnet_item['is-shared']
      
      #TODO: validate instantiation parameters
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
      if nst_json["slice_vld"]:
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
    #vld_record['vim-net-id']  = new_nsir['name'] + "." + vld_item['name'] + ".net." + str(uuid.uuid4())
    vld_record['vim-net-id']  = str(uuid.uuid4())
    vld_record['vim-net-stack'] = []


    if 'mgmt-network' in vld_item.keys():
      vld_record['mgmt-network'] = True
    vld_record['type'] = vld_item['type']
    #TODO: FUTUR WORK: use this parameters to define characterisitics (currently not necessary)
    #vld_record['root-bandwidth']
    #vld_record['leaf-bandwidth']
    #vld_record['physical-network']
    #vld_record['segmentation_id']
    vld_record['vld-status'] = 'INACTIVE'
    
    # Defines the parameters 'ns-conn-point-ref' & 'access_net' of each slice_vld
    cp_refs_list = []
    for cp_ref_item in vld_item['nsd-connection-point-ref']:
      cp_dict = {}
      cp_dict[cp_ref_item['subnet-ref']] = cp_ref_item['nsd-cp-ref']
      cp_refs_list.append(cp_dict)
      
      # if the slice defines the accessability (floating IPs) take it, else take it from the NSs.
      if vld_item.get('access_net'):
        vld_record['access_net'] = vld_item['access_net']
      else:
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
                    # If NSD has no 'access_net' parameter, apply True
                    vld_record['access_net'] = True
    
    vld_record['ns-conn-point-ref'] = cp_refs_list
    vld_record['shared-nsrs-list'] = []
    vldr_list.append(vld_record)

  # SHARED functionality: looking for the already shared vld
  # modify the vldr only for those where an instantiated shared ns is conencted
  nsirs_ref_list = nsi_repo.get_all_saved_nsi()
  if nsirs_ref_list:
    for nsr_item in new_nsir['nsr-list']:
      if nsr_item['isshared']:
        # looks for the nsir with the current shared nsr
        for nsir_ref_item in nsirs_ref_list:
          if nsir_ref_item['vldr-list'] and nsir_ref_item['nsi-status'] in ['NEW', 'INSTANTIATING', 'INSTANTIATED', 'READY']:
            nsir_found = False
            for nsr_ref_item in nsir_ref_item['nsr-list']:
              if (nsr_item['subnet-nsdId-ref'] == nsr_ref_item.get('subnet-nsdId-ref') and nsr_ref_item.get('isshared')):
                nsir_found = True
                break
          
            if nsir_found:
              for vld_nsr_item in nsr_item['vld']:
                for vldr_ref in nsir_ref_item['vldr-list']:
                  if vld_nsr_item['vld-ref'] == vldr_ref['id']:
                    for current_vldr_item in vldr_list:
                      if current_vldr_item['id'] == vldr_ref['id']:
                        current_vldr_item['vim-net-id'] = vldr_ref['vim-net-id']
                        current_vldr_item['vim-net-stack'] = vldr_ref['vim-net-stack']
                        current_vldr_item['vld-status'] = 'ACTIVE'
                        current_vldr_item['type'] = vldr_ref['type']
                        current_vldr_item['shared-nsrs-list'] = vldr_ref['shared-nsrs-list']
                        break
              break
  new_nsir['vldr-list'] = vldr_list
  
  return new_nsir

# does the NSs placement based on the available VIMs resources & the required of each NS.
def nsi_placement(new_nsir):

  def check_vim (check_vim, check_list):
    for check_list_item in check_list:
      for check_vimaccountid_item in check_list_item['vimAccountId']:
        if check_vimaccountid_item['vim-id'] == check_vim:
          return True
    
    return False

  # get the VIMs information registered to the SP
  vims_list = mapper.get_vims_info()
  vims_list_len = len(vims_list['vim_list'])

  # validates if the incoming vim_list is empty (return 500) or not (follow)
  if not vims_list['vim_list']:
    return_msg = {}
    return_msg['error'] = "Not found any VIM information, register one to the SP."
    return return_msg, 500

  # NSR placement based on the required nsr resources vs available vim resources
  for nsr_item in new_nsir['nsr-list']:
    # if NOT shared placement is always done. If shared, only the first time (nsr-placement is empty)
    if (not nsr_item['isshared'] or nsr_item['isshared'] and not nsr_item['nsr-placement']):
      vim_found = False
      nsr_placement_list = []
      req_core = req_mem = req_sto = 0
      nsd_obj = mapper.get_nsd(nsr_item['subnet-nsdId-ref'])
      if nsd_obj:
        # prepares the nsr-placement object and gathers the VIMS resources values
        for vnfd_item in nsd_obj['nsd']['network_functions']:
          nsd_comp_dict = {}
          nsd_comp_dict['nsd-comp-ref'] = vnfd_item['vnf_id']
          
          # adds the vnf_id/vim_uuid dict into the slice.nsr-list information
          nsr_placement_list.append(nsd_comp_dict)
          
          # it must return a list of one element as the trio (name/vendor/version) makes it unique
          vnfd_obj = mapper.get_vnfd(vnfd_item['vnf_name'], vnfd_item['vnf_vendor'], vnfd_item['vnf_version'])
          if vnfd_obj:
            vnfd_info = vnfd_obj[0]['vnfd']
            if vnfd_info.get('virtual_deployment_units'):
              for vdu_item in vnfd_info['virtual_deployment_units']:
                # sums up al the individual VNF resources requirements into a total NS resources required
                req_core = req_core + vdu_item['resource_requirements']['cpu']['vcpus']
                if vdu_item['resource_requirements']['memory']['size_unit'] == "MB":
                  req_mem = req_mem + vdu_item['resource_requirements']['memory']['size']/1024
                else:
                  req_mem = req_mem + vdu_item['resource_requirements']['memory']['size']
                if vdu_item['resource_requirements']['storage']['size_unit'] == "MB":
                  req_sto = req_sto + vdu_item['resource_requirements']['storage']['size']/1024
                else:
                  req_sto = req_sto + vdu_item['resource_requirements']['storage']['size']
            
            elif vnfd_info.get('cloudnative_deployment_units'):
              # CNF does not need to look for resources to select VIM.
              pass
            
            else:
              new_nsir['errorLog'] = "VNF type not accepted for placement, only VNF and CNF."
              new_nsir['nsi-status'] = 'ERROR'
              # 409 = The request could not be completed due to a conflict with the current state of the resource.
              return new_nsir, 409

          else:
            new_nsir['errorLog'] = "No VNFD/CNFD available, please use a NSD with available VNFDs."
            new_nsir['nsi-status'] = 'ERROR'
            # 409 = The request could not be completed due to a conflict with the current state of the resource.
            return new_nsir, 409

      else:
        new_nsir['errorLog'] = "No " + str(nsr_item['subnet-nsdId-ref']) + " NSD FOUND."
        new_nsir['nsi-status'] = 'ERROR'
        # 409 = The request could not be completed due to a conflict with the current state of the resource.
        return new_nsir, 409

      for vim_index, vim_item in enumerate(vims_list['vim_list']):
        #TODO: missing to use storage but this data is not comming in the VIMs information
        #if (req_core != 0 and req_mem != 0 and req_sto != 0 and vim_item['type'] == "vm"): #current nsr only has VNFs
        if (req_core != 0 and req_mem != 0 and vim_item['type'] == "vm"):
          available_core = vim_item['core_total'] - vim_item['core_used']
          available_memory = vim_item['memory_total'] - vim_item['memory_used']
          #available_storage = vim_item['storage_total'] - vim_item['storage_used']
          
          #if req_core > available_core or req_mem > available_memory or req_sto > available_storage:
          if req_core > available_core or req_mem > available_memory:
            # if there are no more VIMs in the list, returns error
            if vim_index == (vims_list_len-1):
              new_nsir['errorLog'] = str(nsr_item['nsrName']) + " nsr placement failed, no VIM resources available."
              new_nsir['nsi-status'] = 'ERROR'
              return new_nsir, 409
            else:
              continue
          else:
            # assigns the VIM to the NSr and adds it ninto the list for the NSIr
            selected_vim = vim_item['vim_uuid']
            vim_found = True
            
            # updates resources info in the temp_vims_list json to have the latest info for the next assignment
            vim_item['core_used'] = vim_item['core_used'] + req_core    
            vim_item['memory_used'] = vim_item['memory_used'] + req_mem
            #vim_item['storage_used'] = vim_item['storage_used'] + req_sto
        
        # CNFs placement compares & finds the most resource free VIM available and deploys all CNFs in the VNF   
        elif (req_core == 0 and req_mem == 0 and vim_item['type'] == "container"):
          selected_vim = {}
          # if no vim is still selected, take the first one
          if not selected_vim:
            selected_vim = vim_item['vim_uuid']
          # compare the selected vim with the next one in order to find which one has more available resources
          else:
            sel_vim_core = selected_vim['core_total'] - selected_vim['core_used']
            sel_vim_memory = selected_vim['memory_total'] - selected_vim['memory_used']
            challenger_vim_core = vim_item['core_total'] - vim_item['core_used']
            challenger_vim_memory = vim_item['memory_total'] - vim_item['memory_used']
            if (sel_vim_core < challenger_vim_core and sel_vim_memory < challenger_vim_memory):
              # the current VIM has more available resources than the already selected
              selected_vim = vim_item['vim_uuid']
              vim_found = True
        
        else:
          # if there are no more VIMs in the list, returns error
          if vim_index == (vims_list_len-1) and not selected_vim:
            new_nsir['errorLog'] = str(nsr_item['nsrName'])+ " nsr placement failed, no available VIM was found."
            new_nsir['nsi-status'] = 'ERROR'
            return new_nsir, 409

        #the following two vars must be true because CNFs look for the VIM with better conditions while VNFs look for
        #... the first VIM where the NS fits.
        if vim_found and selected_vim:
          break

      for nsr_placement_item in nsr_placement_list:
        # assigns the VIM to the NSr and adds it into the list for the NSIr
        nsr_placement_item['vim-id'] = selected_vim
      
      # assigns the generated placement list to the NSir key
      nsr_item['nsr-placement'] = nsr_placement_list

  # VLDR placement: if two nsr linked to the same vld are placed in different VIMs, the vld must have boths VIMs
  # from each nsir.nsr-list_item.nsr-placement creates the nsir.vldr-list_item.vim-net-stack list.
  for vldr_item in new_nsir['vldr-list']:
    if not vldr_item['vim-net-stack']:
      vim_net_stack_list = []
    else:
      vim_net_stack_list = vldr_item['vim-net-stack']

    vimaccountid_list = []
    for nsr_item in new_nsir['nsr-list']:
      for vld_ref_item in nsr_item['vld']:
        if vld_ref_item['vld-ref'] == vldr_item['id']:
          for nsr_placement_item in nsr_item['nsr-placement']:
            
            # before adding, checks if this vld is already in the vim: True = adds it / False = doesn't add it
            vld_vim = check_vim(nsr_placement_item['vim-id'], vim_net_stack_list)

            # if the vld does not have the curret vim, add it with a new stack
            if not vld_vim:
              # prepares the object in case it has to be added.
              add_vl = {}
              add_vl['vim-id'] = nsr_placement_item['vim-id']
              add_vl['net-created'] = False
              
              # if empty, adds the first element
              if not vimaccountid_list:
                vimaccountid_list.append(add_vl)
              else:
                exist_vl_vimaccountid = False
                for vimAccountId_item in vimaccountid_list:
                  if vimAccountId_item['vim-id'] == nsr_placement_item['vim-id']:
                    exist_vl_vimaccountid = True
                    break
                
                if exist_vl_vimaccountid == False:
                  vimaccountid_list.append(add_vl)

    if vimaccountid_list:
      LOG.info("NSI_MNGR: Adding a VimAccountId into slice!!")
      vim_net_stack_item = {}
      vim_net_stack_item['id']  = str(uuid.uuid4())
      vim_net_stack_item['vimAccountId'] = vimaccountid_list
      vim_net_stack_list.append(vim_net_stack_item)
      vldr_item['vim-net-stack'] = vim_net_stack_list

  # adds all the VIMs IDs into the slice record first level 'datacenter' field.
  # from each nsir.vldr-list_item.vimAccountId list creates the nsir.datacenter list.
  nsi_datacenter_list = []
  LOG.info("NSI_MNGR: new NSI:" + str(new_nsir))
  time.sleep(0.1)
  for vldr_item in new_nsir['vldr-list']:
    for vim_net_stack_item in vldr_item['vim-net-stack']:
      for vimAccountId_item in vim_net_stack_item['vimAccountId']:
        #if empty, add the first VIM
        if not nsi_datacenter_list:
          nsi_datacenter_list.append(vimAccountId_item['vim-id'])
        else:
          existing_vim = False
          for nsi_datacenter_item in nsi_datacenter_list:
            if nsi_datacenter_item == vimAccountId_item['vim-id']:
              existing_vim = True
              break
          
          if existing_vim == False:
            nsi_datacenter_list.append(vimAccountId_item['vim-id'])
  
  new_nsir['datacenter'] = nsi_datacenter_list
  return new_nsir, 200

# Updates a NSI with the latest information coming from the MANO/GK
def update_instantiating_nsi(nsiId, request_json):
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
  LOG.info("NSI_MNGR: Preparing the record to terminate a Network Slice Instance.")
  mutex_slice2db_access.acquire()
  try:
    terminate_nsi = nsi_repo.get_saved_nsi(nsiId)
    if terminate_nsi:
      # if nsi is not in TERMINATING/TERMINATED
      if terminate_nsi['nsi-status'] in ["INSTANTIATED", "INSTANTIATING", "READY", "ERROR"]:
        terminate_nsi['id'] = terminate_nsi['uuid']
        del terminate_nsi['uuid']

        #FUTURE TODO: allow to programm termination
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

          ## CREATES A LIST OF NSRs TO TERMINATE CHECKING IF EACH NSR IS SHARED WITH OTHER NSIRs
          # creates a nsirs list without the current one
          nsirs_ref_list = nsi_repo.get_all_saved_nsi()
          nsirs_list_no_current = []
          for nsir_item in nsirs_ref_list:
            if nsir_item['uuid'] != terminate_nsi['id']:
              nsirs_list_no_current.append(nsir_item)
          
          # checks if each NSR of the current nsir can be terminated depending if it is shared by other nsirs
          termin_nsrids_list = []
          for termin_nsr_item in terminate_nsi['nsr-list']:
            # if there are other nsirs follow, if not terminate nsr
            if nsirs_list_no_current:
              # creates a list of nsirs with only those having the current nsr
              nsirs_list_with_nsr = []
              for nsir_ref_item in nsirs_list_no_current:
                for nsr_ref_item in nsir_ref_item['nsr-list']:
                  if nsr_ref_item['nsrId'] == termin_nsr_item['nsrId']:
                    nsirs_list_with_nsr.append(nsir_ref_item)

              if nsirs_list_with_nsr:
                # from the previous reduced list, creates a list of nsirs with status [INSTANTIATED, INSTANTIATING, READY]
                instantiated_nsirs_list_with_nsr = []
                for nsir_ref_item in nsirs_list_with_nsr:
                  if nsir_ref_item['nsi-status'] in ['INSTANTIATED', 'INSTANTIATING', 'READY']:
                    instantiated_nsirs_list_with_nsr.append(nsir_ref_item)

                if instantiated_nsirs_list_with_nsr:
                  nsr_to_terminate = False
                else:
                  nsr_to_terminate = True
              else:
                nsr_to_terminate = True
            else:
              nsr_to_terminate = True
            
            # if true, there's not other nsirs sharing the current nsr and so, it can be terminated.
            if nsr_to_terminate:
              termin_nsr_item['working-status'] == 'TERMINATING'
              termin_nsrids_list.append(termin_nsr_item['nsrId'])

          # updates the terminating nsi with the latest information
          updated_nsi = nsi_repo.update_nsi(terminate_nsi, nsiId)

          # starts the thread to terminate while sending back the response
          LOG.info("NSI_MNGR: termin_nsrids_list[0]: " +str(termin_nsrids_list))
          thread_ns_termination = thread_ns_terminate(terminate_nsi, termin_nsrids_list)
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
        terminate_nsi['errorLog'] = "This NSI is either terminated or being terminated."
        terminate_value = 404
    else:
      terminate_nsi['errorLog'] = "There is no NSIR in the db."
      terminate_value = 404
  finally:
    mutex_slice2db_access.release()
    return (terminate_nsi, terminate_value)

# Updates a NSI being terminated with the latest information coming from the MANO/GK.
def update_terminating_nsi(nsiId, request_json):
  jsonNSI = nsi_repo.get_saved_nsi(nsiId)
  if (jsonNSI):
    # starts the thread to update termination info within the services
    thread_update_slice_termination = update_slice_termination(nsiId, request_json)
    thread_update_slice_termination.start()
    return (jsonNSI, 200)
  else:
    return_msg = {}
    return_msg['error'] = "There is no NSIR in the db."
    return (return_msg, 404)
  
# Deletes a NST kept in catalogues
def remove_nsi(nsiId):
  LOG.info("NSI_MNGR: Delete NSI with id: " + str(nsiId))
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

# Gets the total number of nsi saved in tng-repositories for the SP analytics
def get_all_nsi_counter():
  LOG.info("NSI_MNGR: Retrieve all existing NSIs counter")
  nsirepo_jsonresponse = nsi_repo.get_all_saved_nsi_counter()
  if (nsirepo_jsonresponse):
    return (nsirepo_jsonresponse, 200)
  else:
    return_msg = {}
    return_msg['counter'] = "0"
    return (return_msg, 200)
