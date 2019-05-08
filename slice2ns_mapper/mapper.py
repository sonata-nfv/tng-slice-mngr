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

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("slicemngr:repo")
LOG.setLevel(logging.INFO)

JSON_CONTENT_HEADER = {'Content-Type':'application/json'}

#################################### GENERAL URLs TO THE GATEKEEPERS #####################################
# Prepare the URL to ask for the available network services to create NST.
def get_base_url_ns_info():
  ip_address = os.environ.get("SONATA_GTK_COMMON")
  port = os.environ.get("SONATA_GTK_COMMON_PORT")
  base_url = 'http://'+ip_address+':'+port
  return base_url
    
# Prepares the URL_requests to manage Network Services instantiations belonging to the NST/NSI
def get_base_url():
  ip_address = os.environ.get("SONATA_GTK_SP")
  port = os.environ.get("SONATA_GTK_SP_PORT")
  base_url = 'http://'+ip_address+':'+port
  return base_url

# Defines wether if we are using sthe Sonata SP Emulator or not.
def use_sonata():
  return os.environ.get("USE_SONATA")

##################################### SERVICES MANAGEMENT REQUESTS #######################################
#TODO: join this request with the next to have just one either to instantiate & terminate
# POST /requests to INSTANTIATE Network Service instance
def net_serv_instantiate(service_data):
  url = get_base_url() + '/requests'
  data_json = json.dumps(service_data)
  
  #REAL or EMULATED usage of Sonata SP 
  if use_sonata() == "True":
    LOG.info("MAPPER: Sending Instanitation request")
    response = requests.post(url, data=data_json, headers=JSON_CONTENT_HEADER)
    if (response.status_code == 201):
      jsonresponse = json.loads(response.text)
    else:
      jsonresponse = {'http_code': response.status_code,'message': response.json()}
    return jsonresponse
  else:
    print ("SONATA EMULATED INSTANTIATION NSI --> URL: " +url+ ", HEADERS: " +str(JSON_CONTENT_HEADER)+ ", DATA: " +str(data_json))
    uuident = uuid.uuid4()
    jsonresponse = json.loads('{"id":"'+str(uuident)+'"}')
    return jsonresponse

# POST /requests to TERMINATE Network Service instance
def net_serv_terminate(service_data):
  url = get_base_url() + "/requests"
  data_json = json.dumps(service_data)
  
  #REAL or EMULATED usage of Sonata SP 
  if use_sonata() == "True":
    LOG.info("MAPPER: Sending Terminate request")
    response = requests.post(url, data=data_json, headers=JSON_CONTENT_HEADER)
    if (response.status_code == 200) or (response.status_code == 201):
      jsonresponse = json.loads(response.text)
    else:
      jsonresponse = {'http_code': response.status_code,'message': response.json()}
    return jsonresponse
  else:
    jsonresponse = "SONATA EMULATED TERMINATE NSI --> URL: " +url+ ",HEADERS: " +str(JSON_CONTENT_HEADER)+ ",DATA: " +str(data)
    return jsonresponse

# POST to call the Gk when a slice is READY (either instantiated or terminated)
def sliceUpdated(slice_callback, json_slice_info):
  url = str(slice_callback)
  data_json = json.dumps(json_slice_info)
  
  LOG.info("MAPPER: Sending Slice updated to GTK")
  response = requests.post(url, data=data_json, headers=JSON_CONTENT_HEADER)
  
  if (response.status_code == 201):
      jsonresponse = json.loads(response.text)
  else:
      jsonresponse = {'http_code': response.status_code,'message': response.json()}
  
  return jsonresponse

#TODO: check if the next two requests are necessary...
# GET /requests to pull the information of all Network Services INSTANCES
def get_all_all_nsr():
  url = get_base_url() + "/requests"

  #REAL or EMULATED usage of Sonata SP 
  if use_sonata() == "True":
    LOG.info("MAPPER: Getting all NetServicesInstances")
    response = requests.get(url, headers=JSON_CONTENT_HEADER)
    if (response.status_code == 200):
        jsonresponse = json.loads(response.text)
    else:
        jsonresponse = {'http_code': response.status_code,'message': response.json()}
    return jsonresponse  
  else:
    jsonresponse = "SONATA EMULATED GET ALL NSI --> URL: " +url+ ",HEADERS: " +str(JSON_CONTENT_HEADER)
    LOG.info(jsonresponse)
    return jsonresponse

# GET /requests/<request_uuid> to pull the information of a single Network Service INSTANCE
def get_requested_nsr(request_uuid):
  url = get_base_url() + "/requests/" + str(request_uuid)

  #REAL or EMULATED usage of Sonata SP 
  if use_sonata() == "True":
    LOG.info("MAPPER: Getting desired NetServicesInstance")
    response = requests.get(url, headers=JSON_CONTENT_HEADER)
    if (response.status_code == 200):
        jsonresponse = json.loads(response.text)
    else:
        jsonresponse = {'http_code': response.status_code,'message': response.json()}
    return jsonresponse
  else:
    print ("SONATA EMULATED GET NSI --> URL: " +url+ ",HEADERS: " +str(JSON_CONTENT_HEADER))
    uuident = uuid.uuid4()
    example_json_result='{"blacklist": "[]","callback": "","created_at": "2018-07-23T08:38:10.544Z","customer_uuid": null,"egresses": "[]","id": "1f5c8d55-651c-49cf-853d-c281dbef5639","ingresses": "[]","instance_uuid": "'+str(uuident)+'","request_type": "CREATE_SERVICE","service": {"name": "myns","uuid": "9ce92c4a-5355-47e0-9ed8-e008c201fdfc","vendor": "eu.5gtango","version": "0.1"},"sla_id": null,"status": "READY","updated_at": "2018-07-23T08:39:17.074Z"}'
    jsonresponse = json.loads(example_json_result)
    return jsonresponse 


##################################### VIM NETWORKS MANAGEMENT REQUESTS #######################################
# request to get all registered VIMs information
'''
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
  url = get_base_url() + '/slices/vims'

  #REAL or EMULATED usage of Sonata SP 
  if use_sonata() == "True":
    response = requests.get(url, headers=JSON_CONTENT_HEADER)
    if (response.status_code == 200):
        jsonresponse = json.loads(response.text)
    else:
        jsonresponse = {'http_code': response.status_code,'message': response.json()}   #TODO: ask José the response
  
    return jsonresponse  
  
  else:
    jsonresponse = "SONATA EMULATED GET VIM INFO --> URL: " +url+ ",HEADERS: " +str(JSON_CONTENT_HEADER)
    LOG.info(jsonresponse)
    return jsonresponse

# request to create the networks for a slice deployment
'''
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
Return: {request_status: "COMPLETE/ERROR", message: empty/"msg"} 
'''
def create_vim_network(network_data):
  url = get_base_url() + '/slices/networks'
  data_json = json.dumps(network_data)

  LOG.info("MAPPER: URL --> " + str(url) + ", data --> " + str(data_json))
  time.sleep(0.1)
  
  #REAL or EMULATED usage of Sonata SP 
  if use_sonata() == "True":
    LOG.info("MAPPER: Sending network creation request")
    time.sleep(0.1)
    response = requests.post(url, data=data_json, headers=JSON_CONTENT_HEADER)
    LOG.info("MAPPER: Networks creation response: " +str(response.text))
    time.sleep(0.1)
    
    if (response.status_code == 201):
      jsonresponse = json.loads(response.text)
    else:
      jsonresponse = {'http_code': response.status_code,'message': response.text}
      LOG.info("MAPPER: Networks creation jsonresponse: " +str(jsonresponse))
      time.sleep(0.1)
    
    return jsonresponse
  
  else:
    print ("SONATA EMULATED INSTANTIATION NSI --> URL: " +url+ ", HEADERS: " +str(JSON_CONTENT_HEADER)+ ", DATA: " +str(data_json))
    uuident = uuid.uuid4()
    jsonresponse = json.loads('{"id":"'+str(uuident)+'"}') #TODO: ask José the response
    return jsonresponse

# request to delete the networks for a slice deployment
'''
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
Return: {request_status: "COMPLETE/ERROR", message: empty/"msg"} 
'''
def delete_vim_network(network_data):
  url = get_base_url() + '/slices/networks'
  data_json = json.dumps(network_data)
  
  #REAL or EMULATED usage of Sonata SP 
  if use_sonata() == "True":
    LOG.info("MAPPER: Sending network management request")
    response = requests.delete(url, data=data_json, headers=JSON_CONTENT_HEADER)
    if (response.status_code == 201):
      jsonresponse = json.loads(response.text)
    else:
      jsonresponse = {'http_code': response.status_code,'message': response.json()}
    return jsonresponse
  else:
    print ("SONATA EMULATED INSTANTIATION NSI --> URL: " +url+ ", HEADERS: " +str(JSON_CONTENT_HEADER)+ ", DATA: " +str(data_json))
    uuident = uuid.uuid4()
    jsonresponse = json.loads('{"id":"'+str(uuident)+'"}') #TODO: ask José the response
    return jsonresponse


################################## REQUEST TO CHECK EXISTING SERVICES ####################################
# GET /services/<uuid> tu pull a single Network Service information
def get_nsd(nsd_uuid):
  LOG.info("MAPPER: Preparing the request to get the NetServices Information")
  url = get_base_url_ns_info() + "/services/" + str(nsd_uuid)

  response = requests.get(url)
    
  if (response.status_code == 200):
      service_response = json.loads(response.text)
  else:
      service_response = {'http_code': response.status_code,'message': response.json()}
  return service_response

# GET /services to pull all Network Services information
def get_nsd_list():
  LOG.info("MAPPER: Preparing the request to get the NetServices Information")
  time.sleep(0.1)
  # cleans the current nsInfo_list to have the information updated
  del db.nsInfo_list[:]
  url = get_base_url_ns_info() + "/services"

  #SONATA SP or EMULATED Mode 
  if use_sonata() == "True":
    response = requests.get(url)
    
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
    return service_response
  else:
    URL_response = "SONATA EMULATED GET SERVICES --> URL: " +url+ ",HEADERS: " +str(JSON_CONTENT_HEADER)
    print (URL_response)
    return URL_response
      
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
