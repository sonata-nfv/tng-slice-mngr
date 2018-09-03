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

import os, sys, requests, json, logging, uuid, time
import database.database as db
import objects.nsd as nsd

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("slicemngr:repo")
LOG.setLevel(logging.INFO)

JSON_CONTENT_HEADER = {'Content-Type':'application/json'}

#################################### Sonata SP information #####################################
#Prepare the URL to ask for the available network services to create NST.
def get_base_url_NetService_info():
    #ip_address=db.settings.get('SONATA_COMPONENTS','SONATA_GTK_COMMON')
    #port = db.settings.get('SONATA_COMPONENTS','SONATA_GTK_COMMON_PORT')
    ip_address = os.environ.get("SONATA_GTK_COMMON")
    port = os.environ.get("SONATA_GTK_COMMON_PORT")
    base_url = 'http://'+ip_address+':'+port
    return base_url
    
#Prepares the URL_requests to manage Network Services instantiations belonging to the NST/NSI
def get_base_url():
    #ip_address=db.settings.get('SONATA_COMPONENTS','SONATA_GTK_SP')
    #port = db.settings.get('SONATA_COMPONENTS','SONATA_GTK_SP_PORT')
    ip_address = os.environ.get("SONATA_GTK_SP")
    port = os.environ.get("SONATA_GTK_SP_PORT")
    base_url = 'http://'+ip_address+':'+port
    return base_url

def use_sonata():
    #return db.settings.get('USE_SONATA')  
    return os.environ.get("USE_SONATA")

########################################## /requests ##########################################
#POST /requests to INSTANTIATE Network Service instance
def net_serv_instantiate(service_data):
    LOG.info("MAPPER: Preparing the request to instantiate NetServices")
    url = get_base_url() + '/requests'
    data_json = json.dumps(service_data)
    #{"uuid":"service_uuid", "ingresses"':[], '"egresses"':[], '"blacklist"':[], "sla_uuid":"sla_uuid"}
    LOG.info("MAPPER: URL is: " + str(url))
    LOG.info("MAPPER: data sent to instantiateNS: " +str(data_json))
    
    #REAL or EMULATED usage of Sonata SP 
    if use_sonata() == "True":
      response = requests.post(url, data=data_json, headers=JSON_CONTENT_HEADER)
      if (response.status_code == 201):
          jsonresponse = json.loads(response.text)
          LOG.info("MAPPER: INSTANTIATING NetServices belonging to the NetSlice: " + str(jsonresponse))
      else:
          error = {'http_code': response.status_code,'message': response.json()}
          jsonresponse = error
          LOG.info('MAPPER: error when instantiating NetService: ' + str(error))
      return jsonresponse
    else:
      print ("SONATA EMULATED INSTANTIATION NSI --> URL: " +url+ ",HEADERS: " +str(JSON_CONTENT_HEADER)+ ",DATA: " +str(data_json))
      #Generates a RANDOM (uuid4) UUID for this emulated NSI
      uuident = uuid.uuid4()
      jsonresponse = json.loads('{"id":"'+str(uuident)+'"}')
      return jsonresponse

#POST /requests to TERMINATE Network Service instance
def net_serv_terminate(servInstance_uuid):
    LOG.info("MAPPER: Preparing the request to terminate NetServices")
    url = get_base_url() + "/requests"
    #data = '{"instance_uuid":'+ servInstance_uuid + ', "request_type":"TERMINATE_SERVICE"}'
    data = {}
    data["instance_uuid"] = str(servInstance_uuid)
    data["request_type"] = "TERMINATE_SERVICE"
    data_json = json.dumps(data)
    LOG.info("MAPPER: URL to terminate NetServices: " +str(url))
    LOG.info("MAPPER: DATA to terminate NetServices: " +str(data))
    
    #REAL or EMULATED usage of Sonata SP 
    if use_sonata() == "True":
      LOG.info("MAPPER: sending terminate request.")
      response = requests.post(url, data=data_json, headers=JSON_CONTENT_HEADER)
      if (response.status_code == 200) or (response.status_code == 201) or (response.status_code == 204):
          jsonresponse = json.loads(response.text)
          LOG.info("MAPPER: NetService belonging the NetSlice TERMINATED: "  + str(jsonresponse))
      else:
          error = {'http_code': response.status_code,'message': response.json()}
          jsonresponse = error
          LOG.info('MAPPER: error when terminating NetService instantiation: ' + str(error))
      return jsonresponse
    else:
      jsonresponse = "SONATA EMULATED TERMINATE NSI --> URL: " +url+ ",HEADERS: " +str(JSON_CONTENT_HEADER)+ ",DATA: " +str(data)
      return jsonresponse

#GET /requests to pull the information of all Network Services INSTANCES
def getAllNetServInstances():
    LOG.info("MAPPER: Preparing the request to get all the NetServicesInstances")
    url = get_base_url() + "/requests"

    #REAL or EMULATED usage of Sonata SP 
    if use_sonata() == "True":
      response = requests.get(url, headers=JSON_CONTENT_HEADER)
      if (response.status_code == 200):
          jsonresponse = json.loads(response.text)
          LOG.info("MAPPER: Information of all instantiated netService received: " + str(jsonresponse))
      else:
          error = {'http_code': response.status_code,'message': response.json()}
          jsonresponse = error
          LOG.info('MAPPER: error when receiving all NS instantiations info: ' + str(error))
      return jsonresponse  
    else:
      jsonresponse = "SONATA EMULATED GET ALL NSI --> URL: " +url+ ",HEADERS: " +str(JSON_CONTENT_HEADER)
      LOG.info(jsonresponse)
      return jsonresponse

#GET /requests/<request_uuid> to pull the information of a single Network Service INSTANCE
def getRequestedNetServInstance(request_uuid):
    LOG.info("MAPPER: Preparing the request to get desired NetServicesInstance")
    url = get_base_url() + "/requests/" + str(request_uuid)

    #REAL or EMULATED usage of Sonata SP 
    if use_sonata() == "True":
      response = requests.get(url, headers=JSON_CONTENT_HEADER)
      if (response.status_code == 200):
          jsonresponse = json.loads(response.text)
          LOG.info("MAPPER: Information of the instantiated netService received: " + str(jsonresponse))
      else:
          error = {'http_code': response.status_code,'message': response.json()}
          jsonresponse = error
          LOG.info('MAPPER: error when receiving the NS instantiation info: ' + str(error))
      return jsonresponse
    else:
      print ("SONATA EMULATED GET NSI --> URL: " +url+ ",HEADERS: " +str(JSON_CONTENT_HEADER))
      uuident = uuid.uuid4()
      example_json_result='{"blacklist": "[]","callback": "","created_at": "2018-07-23T08:38:10.544Z","customer_uuid": null,"egresses": "[]","id": "1f5c8d55-651c-49cf-853d-c281dbef5639","ingresses": "[]","instance_uuid": "'+str(uuident)+'","request_type": "CREATE_SERVICE","service": {"name": "myns","uuid": "9ce92c4a-5355-47e0-9ed8-e008c201fdfc","vendor": "eu.5gtango","version": "0.1"},"sla_id": null,"status": "READY","updated_at": "2018-07-23T08:39:17.074Z"}'
      jsonresponse = json.loads(example_json_result)
      return jsonresponse 
      
      
   
########################################## /services ##########################################
#GET /services to pull all Network Services information
#curl -X GET tng-gtk-common:5000/services
def getListNetServices():
    LOG.info("MAPPER: Preparing the request to get the NetServices Information")
    del db.nsInfo_list[:]                                #cleans the current nsInfo_list to have the information updated
    url = get_base_url_NetService_info() + "/services"
 
    #SONATA SP or EMULATED Mode 
    if use_sonata() == "True":
      response = requests.get(url)
      
      if (response.status_code == 200):
          LOG.info("MAPPER: Services from the SP received.")
          services_array = json.loads(response.text)
          for service_item in services_array:
            nsd=parseNetworkService(service_item)            #Each element of the list is a dictionary
            nsd_string = vars(nsd)
            db.nsInfo_list.append(nsd_string)                #Adds the dictionary element into the list
          service_response = db.nsInfo_list
      else:
          error = {'http_code': response.status_code,'message': response.json()}
          service_response = error
          LOG.info('MAPPER: error when deceiving the SP services information: ' + str(error))  
      return service_response
    else:
      URL_response = "SONATA EMULATED GET SERVICES --> URL: " +url+ ",HEADERS: " + str(JSON_CONTENT_HEADER)
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
