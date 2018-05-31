#!/usr/bin/python
import os, sys, requests, json, logging, time
from flask import jsonify

import database.database as db

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("slicemngr:repo")
LOG.setLevel(logging.INFO)

JSON_CONTENT_HEADER = {'Content-Type':'application/json'}

#################################### Sonata Repositories information #####################################
def get_base_url():
    #http://tng-rep:4012/records/nsir/ns-instances
    ip_address=db.settings.get('SONATA_COMPONENTS','SONATA_REP')
    port = db.settings.get('SONATA_COMPONENTS','SONATA_REP_PORT')
    base_url = 'http://'+ip_address+':'+port
    return base_url


####################################### /records/nsir/ns-instances #######################################
#POST to send the NSI information to the repositories
def safe_nsi(NSI_string):
    LOG.info("NSI_MNGR2REPO: Sending information to the repositories")
    url = get_base_url() + '/records/nsir/ns-instances'
    data = json.dumps(NSI_string)
    response = requests.post(url, data, headers=JSON_CONTENT_HEADER, timeout=1.0, )
    jsonresponse = json.loads(response.text)
    
    if (response.status_code == 200):                                              #TODO: change the value according to tng-rep when this will be changed
        LOG.info("NSI_MNGR2REPO: NSIR storage accepted.")
    else:
        error = {'http_code': response.status_code,
                 'message': response.json()}
        jsonresponse = error
        LOG.info('NSI_MNGR2REPO: nsir to repo failed: ' + str(error))
    
    return jsonresponse


#GET all NSI information from the repositories
def getAll_saved_nsi():
    LOG.info("NSI_MNGR2REPO: Requesting all NSIs information from repositories")
    url = get_base_url() + '/records/nsir/ns-instances'
    response = requests.get(url, headers=JSON_CONTENT_HEADER)
    LOG.info(response.text)
    jsonresponse = json.loads(response.text)
    
    if (response.status_code == 200):                                              #TODO: change the value according to tng-rep when this will be changed
        LOG.info("NSI_MNGR2REPO: all NSIR received.")
    else:
        error = {'http_code': response.status_code,
                 'message': response.json()}
        jsonresponse = error
        LOG.info('NSI_MNGR2REPO: nsir getAll from repo failed: ' + str(error))
    
    return jsonresponse


######################## /records/nsir/ns-instances/<service_instance_uuid> #############################
#GET specific NSI information from the repositories
def get_saved_nsi(nsiId):
    LOG.info("NSI_MNGR2REPO: Requesting NSI information from repositories")
    url = get_base_url() + '/records/nsir/ns-instances/' + nsiId
    response = requests.get(url, headers=JSON_CONTENT_HEADER)
    jsonresponse = json.loads(response.text)
    
    if (response.status_code == 200):                                              #TODO: change the value according to tng-rep when this will be changed
        LOG.info("NSI_MNGR2REPO: NSIR received.")
    else:
        error = {'http_code': response.status_code,
                 'message': response.json()}
        jsonresponse = error
        LOG.info('NSI_MNGR2REPO: nsir get from repo failed: ' + str(error))
    
    return jsonresponse

#PUT update specific NSI information in repositories
def update_nsi(update_NSI, nsiId):
    LOG.info("NSI_MNGR2REPO: Updating NSI information")
    
    url = get_base_url() + '/records/nsir/ns-instances/' + nsiId
    data = json.dumps(update_NSI)
    
    response = requests.put(url, data, headers=JSON_CONTENT_HEADER, timeout=1.0, )
    jsonresponse = json.loads(response.text)
    
    if (response.status_code == 200):                                              #TODO: change the value according to tng-rep when this will be changed
        LOG.info("NSI_MNGR2REPO: NSIR updated.")
    else:
        error = {'http_code': response.status_code,
                 'message': response.json()}
        jsonresponse = error
        LOG.info('NSI_MNGR2REPO: nsir update action to repo failed: ' + str(error))
    
    return jsonresponse

#DELETE soecific NSI information in repositories
def delete_nsi(nsiId):
    LOG.info("NSI_MNGR2REPO: Deleting NSI")
    url = get_base_url() + '/records/nsir/ns-instances/' + nsiId
    response = requests.delete(url)
    LOG.info(response.status_code)
    
    if (response.status_code == 200):                                              #TODO: change the value according to tng-rep when this will be changed
        LOG.info("NSI_MNGR2REPO: NSIR deleted.")
    else:
        error = {'http_code': response.status_code,
                 'message': response.json()}
        response = error
        LOG.info('NSI_MNGR2REPO: nsir delete action to repo failed: ' + str(error))
    
    return response.status_code