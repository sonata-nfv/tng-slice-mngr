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
    ip_address=db.settings.get('SONATA_COMPONENTS','SONATA_GTK_COMMON')
    port = db.settings.get('SONATA_COMPONENTS','SONATA_GTK_COMMON_PORT')
    base_url = 'http://'+ip_address+':'+port
    return base_url
    
#Prepares the URL_requests to manage Network Services instantiations belonging to the NST/NSI
def get_base_url():   
    ip_address=db.settings.get('SONATA_COMPONENTS','SONATA_GTK_SP')
    port = db.settings.get('SONATA_COMPONENTS','SONATA_GTK_SP_PORT') 
    base_url = 'http://'+ip_address+':'+port+'/api/v3'                                                      #TODO: delete '/api/v3' when the "id:None" problem is solved
    return base_url

def use_sonata():    
    return db.settings.get('SLICE_MGR','USE_SONATA')

########################################## /requests ##########################################
#POST /requests to INSTANTIATE Network Service instance
def net_serv_instantiate(service_uuid):
    LOG.info("MAPPER: Preparing the request to instantiate NetServices")
    url = get_base_url() + '/requests'
    data_json = {}
    data_json['uuid'] = service_uuid
    #data_json = json.dumps(data)
    #data_json = {"uuid":" + service_uuid + '", "ingresses"':[], '"egresses"':[], '"blacklist"':[]}            #TODO: create function to add ingresses/egresses/blacklist
    #data_json = {'uuid':'', 'ingresses':[], 'egresses':[],'blacklist':[]}
    #data_json ["uuid"] = service_uuid
    LOG.info("MAPPER: URL is: " + str(url))
    LOG.info("MAPPER: data sent to instantiateNS: " +str(data_json))
    

    #REAL or EMULATED usage of Sonata SP 
    if use_sonata() == "True":
      response = requests.post(url, data=data_json, headers=JSON_CONTENT_HEADER, timeout=1.0, )
      if (response.status_code == 201):
          jsonresponse = json.loads(response.text)
          LOG.info("MAPPER: INSTANTIATING NetServices belonging to the NetSlice: " + str(jsonresponse))
      else:
          error = {'http_code': response.status_code,'message': response.json()}
          jsonresponse = error
          LOG.info('MAPPER: error when instantiating NetService: ' + str(error))
      return jsonresponse

    else:
      print ("SONATA EMULATED INSTANTIATION NSI --> URL: " +url+ ",HEADERS: " +str(JSON_CONTENT_HEADER)+ ",DATA: " +str(data))
      #Generates a RANDOM (uuid4) UUID for this emulated NSI
      uuident = uuid.uuid4()
      jsonresponse = json.loads('{"id":"'+str(uuident)+'"}')
      return jsonresponse

#POST /requests to TERMINATE Network Service instance
def net_serv_terminate(servInstance_uuid):
    LOG.info("MAPPER: Preparing the request to terminate NetServices")
    url = get_base_url() + "/requests"
    data = '{"service_instance_uuid":'+ servInstance_uuid + ', "request_type":"TERMINATE"}'

    #REAL or EMULATED usage of Sonata SP 
    if use_sonata() == "True":
      response = requests.post(url, headers=JSON_CONTENT_HEADER, data=data)
      if (response.status_code == 200) or (response.status_code == 201)or (response.status_code == 204):
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
      example_json_result='{"began_at": "2017-09-15","callback": "http://localhost:5400/serv-instan-time","created_at": "2017-09-15","id": "de0d4c7e-9450-4c3f-8add-5f9531303c65","request_type": "CREATE","service_instance_uuid": "'+str(uuident)+'","service_uuid": "233cb9b2-5575-4ddd-8bd6-6c32396afe02","status": "READY","updated_at": "2017-09-15"}'
      jsonresponse = json.loads(example_json_result)
      return jsonresponse 
      
   
########################################## /services ##########################################
#GET /services to pull all Network Services information
#curl -X GET tng-gtk-common:5000/services
def getListNetServices():
    LOG.info("MAPPER: Preparing the request to get the NetServices Information")
    del db.nsInfo_list[:]                                #cleans the current nsInfo_list to have the information updated
    url = get_base_url_NetService_info() + "/services"
 
    if use_sonata() == "True":                           #SONATA SP or EMULATED Mode
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
