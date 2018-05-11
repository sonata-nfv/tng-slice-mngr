#!/usr/bin/python

import os, sys, requests, json, logging


#################################### Sonata Repositories information #####################################
def get_base_url():
    #http://tng-rep:4012/records/nsir/ns-instances
    ip_address=db.settings.get('SLICE_MGR','SONATA_REPO')
    base_url = 'http://'+ip_address+':4012'
    
    return base_url


####################################### /records/nsir/ns-instances #######################################
#POST to send the NSI information to the repositories
def safe_nsi(NSI_string):
    #curl -X POST -H "Content-type:application/json" --data-binary @spec/fixtures/nsir-example.json <base URL>/records/nsir/ns-instances
    # prepares the parameters for the POST request
    url = get_base_url() + '/records/nsir/ns-instances'
    headers = {"content-type":"application/json"}
    data = jsonify(vars(NSI_string))
    
    response = requests.post(url, headers, data)
    jsonresponse = json.loads(response.text)
    
    return jsonresponse

#GET to get the NSI information from the repositories
def request_saved_nsi():
    #curl -X GET -H "Content-type:application/json" <base URL>/records/nsir/ns-instances
    # prepares the parameters for the POST request
    url = get_base_url() + '/records/nsir/ns-instances'
    headers = {"content-type":"application/json"}
    
    response = requests.get(url, headers)
    jsonresponse = json.loads(response.text)
    
    return jsonresponse

  
######################## /records/nsir/ns-instances/<service_instance_uuid> #############################
#curl -X GET -H "Content-type:application/json" <base URL>/records/nsir/ns-instances/<service_instance_uuid>


#curl -X PUT -H "Content-type:application/json" <base URL>/records/nsir/ns-instances/<service_instance_uuid> -d '{"id":<service uuid>,"descriptor_version":<latest service descriptor version>,"version":<version>,"vendor":<vendor>,"name":<name>,"<field_to_be_updated>":<value>}'


#curl -X DELETE <base URL>/records/nsir/ns-instances/<service_instance_uuid>