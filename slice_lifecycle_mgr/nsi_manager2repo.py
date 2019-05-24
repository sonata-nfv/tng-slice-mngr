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

# Returns the last URL version to send reqauests to the Repositories Docker
def get_base_url():
    ip_address = os.environ.get("SONATA_REP")
    port = os.environ.get("SONATA_REP_PORT")
    base_url = 'http://'+ip_address+':'+port
    return base_url

# POST to send the NSI information to the repositories
def safe_nsi(NSI_dict):
    url = get_base_url() + '/records/nsir/ns-instances'
    data = json.dumps(NSI_dict)
    response = requests.post(url, data, headers=JSON_CONTENT_HEADER)
    jsonresponse = json.loads(response.text)
    LOG.info("NSI_MNGR:  jsonresponse: " +str(jsonresponse))
    time.sleep(0.1)
    
    if(response.status_code != 200):
        jsonresponse = {'http_code': response.status_code,'message': response.json()}
        LOG.info('NSI_MNGR2REPO: nsir to repo failed: ' + str(jsonresponse))
    
    return jsonresponse

# GET all NSI items from the repositories
def get_all_saved_nsi():
    url = get_base_url() + '/records/nsir/ns-instances'
    response = requests.get(url, headers=JSON_CONTENT_HEADER)
    jsonresponse = json.loads(response.text)
    
    if(response.status_code != 200):
        jsonresponse = {'http_code': response.status_code,'message': response.json()}
        LOG.info('NSI_MNGR2REPO: nsir getAll from repo failed: ' + str(jsonresponse))
    
    return jsonresponse

# GET specific NSI item from the repositories
def get_saved_nsi(nsiId):
    url = get_base_url() + '/records/nsir/ns-instances/' + nsiId
    response = requests.get(url, headers=JSON_CONTENT_HEADER)
    jsonresponse = json.loads(response.text)
    LOG.info('NSI_MNGR2REPO: nsir get from repo: ' + str(jsonresponse))
    
    if(response.status_code != 200):
        jsonresponse = {'http_code': response.status_code,'message': response.json()}
        LOG.info('NSI_MNGR2REPO: nsir get from repo failed: ' + str(jsonresponse))
    
    return jsonresponse

# PUT to update specific NSI information in repositories
def update_nsi(update_NSI, nsiId):
    time.sleep(0.1)
    url = get_base_url() + '/records/nsir/ns-instances/' + nsiId
    data = json.dumps(update_NSI)

    response = requests.put(url, data, headers=JSON_CONTENT_HEADER, timeout=1.0, )
    jsonresponse = json.loads(response.text)
    
    if(response.status_code != 200):
        jsonresponse = {'http_code': response.status_code,'message': response.json()}
        LOG.info('NSI_MNGR2REPO: nsir update action to repo failed: ' + str(jsonresponse))
    
    return jsonresponse

# DELETE soecific NSI item in repositories
def delete_nsi(nsiId):
    time.sleep(0.1)
    url = get_base_url() + '/records/nsir/ns-instances/' + nsiId
    jsonresponse = requests.delete(url)
    
    if(response.status_code != 200):
        jsonresponse = {'http_code': response.status_code,'message': response.json()}
        LOG.info('NSI_MNGR2REPO: nsir delete action to repo failed: ' + str(jsonresponse))
    
    return jsonresponse.status_code