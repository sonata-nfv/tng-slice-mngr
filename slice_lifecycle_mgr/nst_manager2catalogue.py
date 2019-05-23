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

import os, sys, requests, json, logging, time
from flask import jsonify

import database.database as db

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("slicemngr:repo")
LOG.setLevel(logging.INFO)

JSON_CONTENT_HEADER = {'Content-Type':'application/json'}

# Returns the last URL version to send reqauests to the Catalogues Docker
def get_base_url():
    ip_address = os.environ.get("SONATA_CAT")
    port = os.environ.get("SONATA_CAT_PORT")
    base_url = 'http://'+ip_address+':'+port
    
    return base_url

# POST to send the NST information to the catalogues
def safe_nst(nst_string):
    LOG.info("NST_MNGR2CAT: Sending information to the catalogues")
    url = get_base_url() + '/api/catalogues/v2/nsts'
    data = json.dumps(nst_string)
    response = requests.post(url, data, headers=JSON_CONTENT_HEADER, timeout=1.0, )
    jsonresponse = json.loads(response.text)
    
    if (response.status_code != 201):
        error = {'http_code': response.status_code,'message': response.json()}
        jsonresponse = error
        LOG.info('NST_MNGR2CAT: nstd to catalogues failed: ' + str(error))
    
    return jsonresponse, response.status_code
       
# GET all NST information from the catalogues
def get_all_saved_nst():
    LOG.info("NST_MNGR2CAT: Requesting all NSTD information from catalogues")
    url = get_base_url() + '/api/catalogues/v2/nsts'
    response = requests.get(url, headers=JSON_CONTENT_HEADER)
    jsonresponse = json.loads(response.text)
    
    if (response.status_code != 200):
        jsonresponse = {'http_code': response.status_code,'message': response.json()}
        LOG.info('NSI_MNGR2CAT: nstd getAll from catalogues failed: ' + str(jsonresponse))
    
    return jsonresponse
    
# PUT to update specific NST parameter in catalogues
# The url follows this rule(.../nsts/<nstId>/?nstParameter2update) where nstParameter2update is...
# ... a string following the structure: "<key>=<value>"
def update_nst(nstParameter2update, nstId):
    LOG.info("NST_MNGR2CAT: Updating NSTD information")
    url = get_base_url() + '/api/catalogues/v2/nsts/' + nstId + '?' + nstParameter2update
    jsonresponse = requests.put(url, headers=JSON_CONTENT_HEADER, timeout=1.0, )
    
    if (jsonresponse.status_code == 200) or (jsonresponse.status_code == 201):
        LOG.info("NST_MNGR2CAT: NSTD updated.")
    else:
        jsonresponse = {'http_code': jsonresponse.status_code,'message': jsonresponse.json()}
        LOG.info('NST_MNGR2CAT: nstd update action to catalogues failed: ' + str(jsonresponse))
    return jsonresponse

# GET the specific NST item from the catalogues
def get_saved_nst(nstId):
    LOG.info("NST_MNGR2CAT: Requesting NST information from catalogues")
    url = get_base_url() + '/api/catalogues/v2/nsts/' + nstId
    response = requests.get(url, headers=JSON_CONTENT_HEADER)
    jsonresponse = json.loads(response.text)
    
    if (response.status_code != 200):
        jsonresponse = json.loads(response.text)
        jsonresponse['http_code'] = response.status_code
        LOG.info('NST_MNGR2CAT: nstd get from catalogue failed: ' + str(jsonresponse))
    
    return jsonresponse
    
# DELETE the specific NST item from catalogues
def delete_nst(nstId):
    LOG.info("NST_MNGR2CAT: Deleting NSTD")
    url = get_base_url() + '/api/catalogues/v2/nsts/' + nstId
    response = requests.delete(url)
    LOG.info(response.status_code)
    
    if (response.status_code != 200):
        response = {'http_code': response.status_code,'message': response.json()}
        LOG.info('NST_MNGR2CAT: nstd delete action to catalogues failed: ' + str(response))
    
    return response
  
  
################################## OTHER OPTIONS TO WORK IN THE FUTURE ################################
#GET 	  /api/catalogues/v2/{collection}?{attributeName}={value}  --> Lists all descriptors matching a specific filter(s)
#GET 	  /api/catalogues/v2/{collection}?version=last             --> Lists only the last version for all descriptors
#PUT 	  /api/catalogues/v2/{collection}/{id}                     --> Updates a descriptor using the UUID
#PUT 	  /api/catalogues/v2/{collection}/{id}                     --> Sets status of a descriptor using the UUID
#DELETE /api/catalogues/v2/{collection}                          --> Deletes a descriptor using the naming triplet, i.e., name, vendor & version


