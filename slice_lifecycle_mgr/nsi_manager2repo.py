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
import os, sys, requests, json, logging, time
from flask import jsonify

import database.database as db

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("slicemngr:repo")
LOG.setLevel(logging.INFO)

JSON_CONTENT_HEADER = {'Content-Type':'application/json'}

#################################### Sonata Repositories information #####################################
def get_base_url():
    ip_address = os.environ.get("SONATA_REP")
    port = os.environ.get("SONATA_REP_PORT")
    base_url = 'http://'+ip_address+':'+port
    return base_url


####################################### /records/nsir/ns-instances #######################################
#POST to send the NSI information to the repositories
def safe_nsi(NSI_string):
    LOG.info("NSI_MNGR2REPO: Sending information to the repositories")
    url = get_base_url() + '/records/nsir/ns-instances'
    data = json.dumps(NSI_string)
    response = requests.post(url, data, headers=JSON_CONTENT_HEADER)
    jsonresponse = json.loads(response.text)
    
    if (response.status_code == 200):
        LOG.info("NSI_MNGR2REPO: NSIR storage accepted.")
    else:
        error = {'http_code': response.status_code,'message': response.json()}
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
    
    if (response.status_code == 200):
        LOG.info("NSI_MNGR2REPO: all NSIR received.")
    else:
        error = {'http_code': response.status_code,'message': response.json()}
        jsonresponse = error
        LOG.info('NSI_MNGR2REPO: nsir getAll from repo failed: ' + str(error))
    
    return jsonresponse


######################## /records/nsir/ns-instances/<service_instance_uuid> #############################
#GET specific NSI information from the repositories
def get_saved_nsi(nsiId):
    LOG.info("NSI_MNGR2REPO: Requesting NSI information from repositories")
    time.sleep(0.1)
    url = get_base_url() + '/records/nsir/ns-instances/' + nsiId
    response = requests.get(url, headers=JSON_CONTENT_HEADER)
    jsonresponse = json.loads(response.text)
    
    if (response.status_code == 200):
        LOG.info("NSI_MNGR2REPO: NSIR received.")
        time.sleep(0.1)
    else:
        error = {'http_code': response.status_code,'message': response.json()}
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
    
    if (response.status_code == 200):
        LOG.info("NSI_MNGR2REPO: NSIR updated.")
    else:
        error = {'http_code': response.status_code,'message': response.json()}
        jsonresponse = error
        LOG.info('NSI_MNGR2REPO: nsir update action to repo failed: ' + str(error))
    
    return jsonresponse

#DELETE soecific NSI information in repositories
def delete_nsi(nsiId):
    LOG.info("NSI_MNGR2REPO: Deleting NSI")
    url = get_base_url() + '/records/nsir/ns-instances/' + nsiId
    response = requests.delete(url)
    LOG.info(response.status_code)
    
    if (response.status_code == 200):
        LOG.info("NSI_MNGR2REPO: NSIR deleted.")
    else:
        error = {'http_code': response.status_code,'message': response.json()}
        response = error
        LOG.info('NSI_MNGR2REPO: nsir delete action to repo failed: ' + str(error))
    
    return response.status_code