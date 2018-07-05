#!/usr/bin/python
import os, sys, requests, json, logging, time
from flask import jsonify

import database.database as db

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("slicemngr:repo")
LOG.setLevel(logging.INFO)

JSON_CONTENT_HEADER = {'Content-Type':'application/json'}

#################################### Sonata Catalogues information ###################################
def get_base_url():
    #ip_address=db.settings.get('SONATA_COMPONENTS','SONATA_CAT')
    #port = db.settings.get('SONATA_COMPONENTS','SONATA_CAT_PORT')
    ip_address = os.environ.get("SONATA_CAT")
    port = os.environ.get("SONATA_CAT_PORT")
    base_url = 'http://'+ip_address+':'+port
    return base_url
    
####################################### /api/catalogues/v2/nsts ######################################
#POST to send the NST information to the catalogues
def safe_nst(nst_string):
    LOG.info("NST_MNGR2CAT: Sending information to the catalogues")
    url = get_base_url() + '/api/catalogues/v2/nsts'
    data = json.dumps(nst_string)
    response = requests.post(url, data, headers=JSON_CONTENT_HEADER, timeout=1.0, )
    jsonresponse = json.loads(response.text)
    
    if (response.status_code == 201):
        LOG.info("NST_MNGR2CAT: NSTD storage accepted.")
    else:
        error = {'http_code': response.status_code,'message': response.json()}
        jsonresponse = error
        LOG.info('NST_MNGR2CAT: nstd to catalogues failed: ' + str(error))
    return jsonresponse
       
#GET all NST information from the catalogues
def getAll_saved_nst():
    LOG.info("NST_MNGR2CAT: Requesting all NSTD information from catalogues")
    url = get_base_url() + '/api/catalogues/v2/nsts'
    response = requests.get(url, headers=JSON_CONTENT_HEADER)
    LOG.info(response.text)
    jsonresponse = json.loads(response.text)
    
    if (response.status_code == 200):
        LOG.info("NST_MNGR2CAT: all NSTD received.")
    else:
        error = {'http_code': response.status_code,'message': response.json()}
        jsonresponse = error
        LOG.info('NSI_MNGR2CAT: nstd getAll from catalogues failed: ' + str(error))
    return jsonresponse
    
#PUT to update specific NST parameter in catalogues
#the url follows this rule(.../nsts/<nstId>/?nstParameter2update) where
#nstParameter2update is a string following the structure: "<key>=<value>"
def update_nst(nstParameter2update, nstId):
    LOG.info("NST_MNGR2CAT: Updating NSTD information")
    url = get_base_url() + '/api/catalogues/v2/nsts/' + nstId + '?' + nstParameter2update
    response = requests.put(url, headers=JSON_CONTENT_HEADER, timeout=1.0, )
    
    if (response.status_code == 200) or (response.status_code == 201):
        LOG.info("NST_MNGR2CAT: NSTD updated.")
    else:
        error = {'http_code': response.status_code,'message': response.json()}
        response = error
        LOG.info('NST_MNGR2CAT: nstd update action to catalogues failed: ' + str(error))
    return response.text


#################################### /api/catalogues/v2/nsts/{id} ####################################
#GET the specific NST information from the catalogues
def get_saved_nst(nstId):
    LOG.info("NST_MNGR2CAT: Requesting NST information from catalogues")
    url = get_base_url() + '/api/catalogues/v2/nsts/' + nstId
    response = requests.get(url, headers=JSON_CONTENT_HEADER)
    jsonresponse = json.loads(response.text)
    
    if (response.status_code == 200):
        LOG.info("NST_MNGR2CAT: NSTD received.")
    else:
        error = {'http_code': response.status_code,'message': response.json()}
        jsonresponse = error
        LOG.info('NST_MNGR2CAT: nstd get from catalogue failed: ' + str(error))
    return jsonresponse
    
#DELETE the specific NST information from catalogues
def delete_nst(nstId):
    LOG.info("NST_MNGR2CAT: Deleting NSTD")
    url = get_base_url() + '/api/catalogues/v2/nsts/' + nstId
    response = requests.delete(url)
    LOG.info(response.status_code)
    
    if (response.status_code == 200):
        LOG.info("NST_MNGR2CAT: NSTD deleted.")
    else:
        error = {'http_code': response.status_code,'message': response.json()}
        response = error
        LOG.info('NST_MNGR2CAT: nstd delete action to catalogues failed: ' + str(error))
    return response.status_code
  
################################## OTHER OPTIONS TO WORK IN THE FUTURE ################################
#GET 	  /api/catalogues/v2/{collection}?{attributeName}={value}  --> Lists all descriptors matching a specific filter(s)
#GET 	  /api/catalogues/v2/{collection}?version=last             --> Lists only the last version for all descriptors
#PUT 	  /api/catalogues/v2/{collection}/{id}                     --> Updates a descriptor using the UUID
#PUT 	  /api/catalogues/v2/{collection}/{id}                     --> Sets status of a descriptor using the UUID
#DELETE /api/catalogues/v2/{collection}                          --> Deletes a descriptor using the naming triplet, i.e., name, vendor & version


