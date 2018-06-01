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
    ip_address=db.settings.get('SONATA_COMPONENTS','SONATA_CAT')
    port = db.settings.get('SONATA_COMPONENTS','SONATA_CAT_PORT')
    base_url = 'http://'+ip_address+':'+port
    return base_url
    
####################################### /api/catalogues/v2/nsts ######################################
#POST to send the NST information to the catalogues
def safe_nst(NST_string):
    LOG.info("NST_MNGR2CAT: Sending information to the catalogues")
    url = get_base_url() + '/api/catalogues/v2/nsts'
    data = json.dumps(NST_string)
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
    
#PUT update specific NST information in catalogues
def update_nst(nst_json, nstId):
    LOG.info("NST_MNGR2CAT: Updating NSTD information")
    time.sleep(.2)
    url = get_base_url() + '/api/catalogues/v2/nsts' + nstId
    LOG.info('NST_MNGR2CAT: this is the URL: ' +url)
    time.sleep(.2)
    data = nst_json
    LOG.info('NST_MNGR2CAT: THE PUT IS SENT AND ITS RESPONSE RECEIVED: ' +str(data))
    time.sleep(.2)
    response = requests.put(url, data, headers=JSON_CONTENT_HEADER, timeout=1.0, )
    LOG.info('NST_MNGR2CAT: STATUS CODE: ' + str(response.status_code))
    LOG.info('NST_MNGR2CAT: TEXT INSIDE THE RESPONSE: ' + str(response.text))
    time.sleep(.2)
    jsonresponse = json.loads(response.text)
    LOG.info('NST_MNGR2CAT: nstd get from catalogue failed: ' + str(jsonresponse))
    time.sleep(.2)
    
    if (response.status_code == 200):
        LOG.info("NST_MNGR2CAT: NSTD updated.")
    else:
        error = {'http_code': response.status_code,'message': response.json()}
        jsonresponse = error
        LOG.info('NST_MNGR2CAT: nstd update action to catalogues failed: ' + str(error))
    
    return jsonresponse


#################################### /api/catalogues/v2/nsts/{id} ####################################
#GET specific NST information from the catalogues
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
    
#DELETE soecific NST information in catalogues
def delete_nsi(nstId):
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
#GET 	  /api/catalogues/v2/{collection}?{attributeName}={value}  --> List all descriptors matching a specific filter(s)
#GET 	  /api/catalogues/v2/{collection}?version=last             --> List only the last version for all descriptors
#PUT 	  /api/catalogues/v2/{collection}/{id}                     --> Update a descriptor using the UUID
#PUT 	  /api/catalogues/v2/{collection}/{id}                     --> Set status of a descriptor using the UUID
#DELETE /api/catalogues/v2/{collection}                          --> Delete a descriptor using the naming triplet, i.e., name, vendor & version


