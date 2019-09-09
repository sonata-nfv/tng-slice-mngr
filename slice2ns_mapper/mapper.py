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

import os, sys, requests, json, logging, uuid, time
import database.database as db
import objects.nsd as nsd
from logger import TangoLogger

JSON_CONTENT_HEADER = {'Content-Type':'application/json'}

#Log definition to make the slice logs idetified among the other possible 5GTango components.
LOG = TangoLogger.getLogger(__name__, log_level=logging.DEBUG, log_json=True)
TangoLogger.getLogger("slicemngr:mapper", logging.DEBUG, log_json=True)
LOG.setLevel(logging.DEBUG)


######################################### URLs PREPARATION #########################################
# Returns the last URL version to send reqauests to the Catalogues Docker
def get_url_catalogues():
  ip_address = os.environ.get("SONATA_CAT")
  port = os.environ.get("SONATA_CAT_PORT")
  base_url = 'http://'+ip_address+':'+port
  return base_url
    
# Prepares the URL_requests to manage Network Services instantiations belonging to the NST/NSI
def get_url_sp_gtk():
  ip_address = os.environ.get("SONATA_GTK_SP")
  port = os.environ.get("SONATA_GTK_SP_PORT")
  base_url = 'http://'+ip_address+':'+port
  return base_url

# Returns the last URL version to send reqauests to the Repositories Docker
def get_url_repositories():
    ip_address = os.environ.get("SONATA_REP")
    port = os.environ.get("SONATA_REP_PORT")
    base_url = 'http://'+ip_address+':'+port
    return base_url

##################################### VIM NETWORKS MANAGEMENT REQUESTS ##############################
'''
Objective: Request to get all registered VIMs information
  Params: null
  Request payload: null
  Return:
  {
    vim_list: [
      {
        vim_uuid: String,
        type: String,
        vim_city: String,
        vim_domain: String,
        vim_name: String,
        vim_endpoint: String,
        memory_total: int,
        memory_used: int,
        core_total: int,
        core_used: int
      }
    ],
    nep_list: [
      {
        nep_uuid: String,
        type: String,
        nep_name: String
      }
    ]
  } 
'''
def get_vims_info():
  LOG.info("MAPPER: Requesting VIMs information.")
  url = get_url_sp_gtk() + '/slices/vims'
  response = requests.get(url, headers=JSON_CONTENT_HEADER)
  
  if (response.status_code == 200):
      jsonresponse = json.loads(response.text)
  else:
      jsonresponse = {'http_code': response.status_code,'message': response.json()}   #TODO: ask José the response

  return jsonresponse

'''
Objective: Request to create the networks for a slice deployment 
  Params: network_data - contains payload with the network characteristics
  Request payload:
  {
    instance_id: String,
    vim_list: [
      {
        uuid: String,
        virtual_links: [
          {
            id: String,
            access: String,
            dhcp: String,
            cidr: String,
            qos: String,
            qos_requirements: {
              bandwidth_limit: { bandwidth: int, bandwidth_unit: String },
              minimum_bandwidth: { bandwidth: int, bandwidth_unit: String }
            }
          }
        ]
      }
    ]
  }
  Return: {status: "COMPLETE/ERROR", message: empty/"msg"} 
'''
def create_vim_network(network_data):
  url = get_url_sp_gtk() + '/slices/networks'
  data_json = json.dumps(network_data)
  response = requests.post(url, data=data_json, headers=JSON_CONTENT_HEADER)
  
  if (response.status_code == 201):
    jsonresponse = json.loads(response.text)
  else:
    jsonresponse = {'status':'ERROR', 'http_code': response.status_code, 'message': response.text}
    LOG.info("MAPPER: Networks creation jsonresponse: " +str(jsonresponse))
    time.sleep(0.1)
  
  return jsonresponse

'''
Objective: Request to delete the networks for a slice deployment
  Params: network_id
  Request payload:
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
  Return: {status: "COMPLETE/ERROR", message: empty/"msg"} 
'''
def delete_vim_network(network_data):
  url = get_url_sp_gtk() + '/slices/networks'
  data_json = json.dumps(network_data)
  response = requests.delete(url, data=data_json, headers=JSON_CONTENT_HEADER)
  
  if (response.status_code == 201):
    jsonresponse = json.loads(response.text)
  else:
    jsonresponse = {'status':'ERROR', 'http_code': response.status_code, 'message': response.text}
    LOG.info("MAPPER: Networks removal jsonresponse: " +str(jsonresponse))
    time.sleep(0.1)

  return jsonresponse

##################################### WIM MANAGEMENT REQUESTS ##############################
'''
Objective: Request to get all registered WIMs information
  Params: 
  Request payload:
  Return:
  [
    {
      "uuid": "String",
      "name": "String",
      "attached_vims": [
        "Strings"
      ],
      "attached_endpoints": [
        "Strings"
      ],
      "qos": [
        {
          "node_1": "String",
          "node_2": "String",
          "latency": "int",
          "latency_unit": "String",
          "bandwidth": "int",
          "bandwidth_unit": "String"
        }
      ]
    }
  ]
'''
def get_wims_info():
  LOG.info("MAPPER: Requesting WIMs information.")
  url = get_url_sp_gtk() + '/slices/wims'
  response = requests.get(url, headers=JSON_CONTENT_HEADER)
  
  if (response.status_code == 200):
      jsonresponse = json.loads(response.text)
  else:
      jsonresponse = {'http_code': response.status_code,'message': response.json()}   #TODO: ask José the response

  return jsonresponse

'''
Objective: Request to create a wim interconnection between vims
  Params: wim_link_data - contains the following json:
  {
    "service_instance_id": "String",
    "wim_uuid": "String",
    "vl_id": "String",
    "ingress": {
      "location": "String",
      "nap": "String"
    },
    "egress": {
      "location": "String",
      "nap": "String"
    },
    "qos": {
      "latency": "int",
      "latency_unit": "String",
      "bandwidth": "int",
      "bandwidth_unit": "String"
    },
    "bidirectional": "bool"
  }
  Return: {status: "COMPLETE/ERROR", message: empty/"msg"} 
'''
def create_wim_network(wim_link_data):
  LOG.info("MAPPER: Sending WAN network creation request")
  url = get_url_sp_gtk() + '/slices/wan-networks'
  data_json = json.dumps(wim_link_data)
  response = requests.post(url, data=data_json, headers=JSON_CONTENT_HEADER)
  
  if (response.status_code == 201):
    jsonresponse = json.loads(response.text)
  else:
    jsonresponse = {'status':'ERROR', 'http_code': response.status_code, 'message': response.text}
    LOG.info("MAPPER: WAN Network creation jsonresponse: " +str(jsonresponse))
    time.sleep(0.1)
  
  return jsonresponse

'''
Objective: Request to delete a wim interconnection between vims
  Params: wim_link_data - contains the following json:
  {
    "service_instance_id": "String",
    "wim_uuid": "String",
    "vl_id": "String"
  }
  Return: {status: "COMPLETE/ERROR", message: empty/"msg"} 
'''
def delete_wim_network(wim_link_data):
  url = get_url_sp_gtk() + '/slices/wan-networks'
  data_json = json.dumps(wim_link_data)
  
  LOG.info("MAPPER: Sending WAN network removal request")
  LOG.info("MAPPER: URL --> " + str(url) + ", data --> " + str(data_json))
  time.sleep(0.1)
  response = requests.delete(url, data=data_json, headers=JSON_CONTENT_HEADER)
  LOG.info("MAPPER: Networks removal response: " +str(response))
  time.sleep(0.1)

  if (response.status_code == 201):
    jsonresponse = json.loads(response.text)
  else:
    jsonresponse = {'status':'ERROR', 'http_code': response.status_code, 'message': response.text}
    LOG.info("MAPPER: WAN Network removal jsonresponse: " +str(jsonresponse))
    time.sleep(0.1)

  return jsonresponse

################################ NETWORK SERVICES REQUESTS/RECORDS ##################################
# POST /requests to INSTANTIATE Network Service instance
def net_serv_instantiate(service_data):
  url = get_url_sp_gtk() + '/requests'
  data_json = json.dumps(service_data)
  response = requests.post(url, data=data_json, headers=JSON_CONTENT_HEADER)
  jsonresponse = json.loads(response.text)
  
  return jsonresponse, response.status_code

# POST /requests to TERMINATE Network Service instance
def net_serv_terminate(service_data):
  url = get_url_sp_gtk() + "/requests"
  data_json = json.dumps(service_data)
  response = requests.post(url, data=data_json, headers=JSON_CONTENT_HEADER)
  
  if (response.status_code == 200) or (response.status_code == 201):
    jsonresponse = json.loads(response.text)
  else:
    jsonresponse = {'http_code': response.status_code,'message': response.json()}
  return jsonresponse

# POST to call the Gk when a slice is READY (either instantiated or terminated)
def sliceUpdated(slice_callback, json_slice_info):
  url = str(slice_callback)
  data_json = json.dumps(json_slice_info)
  response = requests.post(url, data=data_json, headers=JSON_CONTENT_HEADER)
  
  if (response.status_code == 201):
      return json.loads(response.text), 201
  else:
      error_json = {'http_code': response.status_code,'message': response.json()}
      return error_json, response.status_code
  
# GET /requests to pull the information of all Network Services INSTANCES
def get_all_nsr():
  url = get_url_sp_gtk() + "/records/services"
  response = requests.get(url, headers=JSON_CONTENT_HEADER)
  
  if (response.status_code == 200):
      jsonresponse = json.loads(response.text)
  else:
      jsonresponse = {'http_code': response.status_code,'message': response.json()}
  return jsonresponse

# GET /requests/<request_uuid> to pull the information of a single Network Service INSTANCE
def get_nsr(request_uuid):
  url = get_url_sp_gtk() + "/records/services/" + str(request_uuid)
  response = requests.get(url, headers=JSON_CONTENT_HEADER)
  
  if (response.status_code == 200):
      jsonresponse = json.loads(response.text)
  else:
      jsonresponse = {'http_code': response.status_code,'message': response.json()}
  return jsonresponse

#################################### NETWORK FUNCTION ####################################
# GET virtual network function RECORD
def get_vnfr(vnfr_uuid):
  url = get_url_repositories() + "/vnfrs/" + str(vnfr_uuid)
  response = requests.get(url, headers=JSON_CONTENT_HEADER)
    
  if (response.status_code == 200):
    service_response = json.loads(response.text)
  else:
    service_response = json.loads(response.text)
    service_response['http_code'] = response.status_code
    LOG.info('NST_MNGR2CAT: nstd get from catalogue failed: ' + str(service_response))
  return service_response

# GET virtual network function DESCRIPTOR
def get_vnfd(vnfd_name, vnfd_vendor, vnfd_version):
  url = get_url_catalogues() + "/api/v2/vnfs?vendor="+str(vnfd_vendor)+"&name="+str(vnfd_name)+"&version="+str(vnfd_version)
  response = requests.get(url,headers=JSON_CONTENT_HEADER)
    
  if (response.status_code == 200):
    function_response = json.loads(response.text)
  else:
    function_response = json.loads(response.text)
    function_response['http_code'] = response.status_code
    LOG.info('NST_MNGR2CAT: nstd get from catalogue failed: ' + str(function_response))
  return function_response

################################# NETWORK SERVICE DESCRIPTORS #####################################
def get_nsd(nsd_uuid):
  url = get_url_catalogues() + "/api/v2/network-services/" + str(nsd_uuid)
  response = requests.get(url, headers=JSON_CONTENT_HEADER)
    
  if (response.status_code == 200):
    service_response = json.loads(response.text)
  else:
    service_response = json.loads(response.text)
    service_response['http_code'] = response.status_code
    LOG.info('NST_MNGR2CAT: nstd get from catalogue failed: ' + str(service_response))
  return service_response

def get_nsd_list():
  # cleans the current nsInfo_list to have the information updated
  del db.nsInfo_list[:]
  url = get_url_catalogues() + "/api/v2/network-services"
  response = requests.get(url, headers=JSON_CONTENT_HEADER)

  if (response.status_code == 200):
      services_array = json.loads(response.text)
      for service_item in services_array:
        if service_item['nsd'].keys() & {'name', 'vendor', 'version'}:
        #if 'name' not in service_item['nsd']:   # to avoid possible problems with other MANO NSD structures
          # each element of the list is a dictionary
          nsd=parseNetworkService(service_item)
          nsd_string = vars(nsd)
          # adds the dictionary element into the list
          db.nsInfo_list.append(nsd_string)
      
      service_response = db.nsInfo_list
  else:
      service_response = {'http_code': response.status_code,'message': response.json()}
  
  LOG.info("MAPPER: Retrieving all available NSDs: "+str(service_response))
  time.sleep(0.1)
  return service_response
      
def parseNetworkService(service):
  NSD=nsd.nsd_content(service['uuid'],
                      service['nsd']['name'], 
                      service['nsd']['description'], 
                      service['nsd']['vendor'], 
                      service['nsd']['version'],
                      service['md5'],
                      service['nsd']['author'],
                      service['created_at'],
                      service['status'], 
                      service['updated_at'])
  return NSD