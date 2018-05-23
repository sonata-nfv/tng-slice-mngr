#!/usr/bin/python
import os, sys, requests, json, logging
from flask import jsonify

import database.database as db

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("slicemngr:repo")
LOG.setLevel(logging.INFO)



#################################### Sonata Repositories information #####################################
def get_base_url():
    #http://tng-rep:4012/records/nsir/ns-instances
    ip_address=db.settings.get('SLICE_MGR','SONATA_REPO')
    base_url = 'http://'+ip_address+':4012'
    
    return base_url


####################################### /records/nsir/ns-instances #######################################
#POST to send the NSI information to the repositories
def safe_nsi(NSI_string):
    # prepares the parameters for the POST request
    url = get_base_url() + '/records/nsir/ns-instances'
    header = {'Content-Type': 'application/json'}
    data = json.dumps(NSI_string)
    LOG.info(data)
    response = requests.post(url, data, headers=header, timeout=1.0, )
    jsonresponse = json.loads(response.text)
    if (response.status_code == 200):
        LOG.info("NSIR storage accepted.")
    else:
        error = {'http_code': response.status_code,
                 'message': response.json()}
        jsonresponse = error
        LOG.info('nsir to repo failed: ' + str(error))
    return jsonresponse


#GET all NSI information from the repositories
def getAll_saved_nsi():
    # prepares the parameters for the POST request
    url = get_base_url() + '/records/nsir/ns-instances'
    headers = {'Content-Type': 'application/json'}
    
    response = requests.get(url, headers)
    #jsonresponse = json.loads(response.text)
    
    #return jsonresponse
    return response.text

  
######################## /records/nsir/ns-instances/<service_instance_uuid> #############################
#GET specific NSI information from the repositories
def get_saved_nsi(nsiId):
    # prepares the parameters for the GET request
    url = get_base_url() + '/records/nsir/ns-instances/' + nsiId
    headers = {'Content-Type': 'application/json'}

    
    response = requests.get(url, headers)
    #jsonresponse = json.loads(response.text)
    #return jsonresponse
    return response

#curl -X PUT -d '{"id":<service uuid>,"descriptor_version":<latest service descriptor version>,"version":<version>,"vendor":<vendor>,"name":<name>,"<field_to_be_updated>":<value>}'
def update_nsi(updatedata):
    url = get_base_url() + '/records/nsir/ns-instances/' + nsiId
    headers = {'Content-Type': 'application/json'}

    data = updatedata
    
    response = requests.put(url, headers, data)
    
    return response

#curl -X DELETE <base URL>/records/nsir/ns-instances/<service_instance_uuid>
def delete_saved_nsi():
    # prepares the parameters for the GET request
    url = get_base_url() + '/records/nsir/ns-instances/' + nsiId
    
    response = requests.delete(url)
    #jsonresponse = json.loads(response.text)
    #return jsonresponse
    return response