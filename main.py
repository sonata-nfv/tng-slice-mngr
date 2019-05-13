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

from flask import Flask, request, jsonify
import os, sys, logging, json, argparse, time, datetime
from configparser import ConfigParser

import slice_lifecycle_mgr.nst_manager as nst_manager
import slice_lifecycle_mgr.nsi_manager as nsi_manager
import slice_lifecycle_mgr.validate_incoming_json as json_validator
import slice2ns_mapper.mapper as mapper
#import slice2ns_mapper.slicer_wrapper_ia as slicer2ia
from database import database as db                                 #TODO: check if it is still used to remove or not

#TODO: apply logs as the rest of the project (2 options)
####### Option 1
#from logger import TangoLogger
#LOG = TangoLogger.getLogger("slicemngr:repo", log_level=logging.INFO, log_json=True)
####### Option 2
#logging.basicConfig(level=logging.DEBUG)
#LOG = logging.getLogger("k8s-wrapper:main")
#LOG.setLevel(logging.DEBUG)

app = Flask(__name__)

#/api/nst/v1/
#/api/nsilcm/v1/nsi
#/api/slices
API_ROOT="/api"
API_NST="/nst"
API_VERSION="/v1"
API_NSILCM="/nsilcm"
API_NSI="/nsi"
API_slices="/slices"

############################################# NETWORK SLICE PING ############################################
# PING function to validate if the slice-docker is active
@app.route('/pings', methods=['GET'])
def getPings():
  ping_response  = {'alive_since': '2018-07-18 10:00:00 UTC', 'current_time': str(datetime.datetime.now().isoformat())}

  return jsonify(ping_response), 200


########################################## NETWORK SERVICES Actions #########################################
# GETS all the available NetService Descriptors to the Sonata SP
@app.route('/api/services', methods=['GET'])
def getAllNetServ():
  ServDict = mapper.get_nsd_list()
  #LOG.info('Returning all network services')
  logging.info('Returning all network services')

  return jsonify(ServDict), 200


######################################### NETSLICE TEMPLATE Actions #########################################
@app.route(API_ROOT+API_NST+API_VERSION+'/descriptors', methods=['OPTIONS'])
def optionsAllNST():
  return "Allow: OPTIONS, GET, HEAD, POST", 200

@app.route(API_ROOT+API_NST+API_VERSION+'/descriptors/<nstId>', methods=['OPTIONS']) 
def optionsOneNST(nstId):
  return "Allow: OPTIONS, GET, HEAD, POST", 200

# CREATES a NetSlice template(NST)
@app.route(API_ROOT+API_NST+API_VERSION+'/descriptors', methods=['POST']) 
def create_slice_template():
  logging.info("SLICE_MAIN: received json from portal: " + str(request.json))
  
  # validates the fields with uuids (if they are right UUIDv4 format), 400 Bad request / 201 ok
  new_nst = json_validator.validate_create_template(request.json)
  
  if (validationResponse[1] == 201):
    new_nst = nst_manager.create_nst(request.json)
  
  logging.info("SLICE_MAIN: HTTP.TEXT: " + str(new_nst[0]) + " HTTP.VALUE: " + str(new_nst[1]))
  return jsonify(new_nst[0]), new_nst[1]

# GETS for all the NetSlice Templates (NST) information
@app.route(API_ROOT+API_NST+API_VERSION+'/descriptors', methods=['GET'])
def get_all_slice_templates():
  listNST = nst_manager.get_all_nst()

  return jsonify(listNST[0]), listNST[1]

#GETS for a specific NetSlice Template (NST) information
@app.route(API_ROOT+API_NST+API_VERSION+'/descriptors/<nstId>', methods=['GET'])
def get_slice_template(nstId):
  returnedNST = nst_manager.get_nst(nstId)

  return jsonify(returnedNST[0]), returnedNST[1]

# DELETES a NetSlice Template
@app.route(API_ROOT+API_NST+API_VERSION+'/descriptors/<nstId>', methods=['DELETE'])
def delete_slice_template(nstId):
  deleted_NSTid = nst_manager.remove_nst(nstId)
  logging.info("SLICE_MAIN: Delete NST with id: " + str(nstId))
  
  if deleted_NSTid == 403:
    returnMessage = "Not possible to delete, there are NSInstances using this NSTemplate"
  else:
    returnMessage = "NST with ID:" + str(nstId) + "deleted from catalogues."
  return jsonify(returnMessage)


######################################### NETSLICE INSTANCE Actions #########################################
# CREATES/INSTANTIATES a NetSlice instance (NSI)
@app.route(API_ROOT+API_NSILCM+API_VERSION+API_NSI, methods=['POST'])
def create_slice_instance():
  logging.info("SLICE_MAIN: received json with NST_uuid from portal to instantiate: " + str(request.json))
  
  # validates the fields with uuids (if they are right UUIDv4 format), 400 Bad request / 201 ok
  instantiating_nsi = json_validator.validate_create_instantiation(request.json)
  
  if (instantiating_nsi[1] == 200):
    instantiating_nsi = nsi_manager.create_nsi(request.json)
  
  logging.info("SLICE_MAIN: HTTP.TEXT: " + str(instantiating_nsi[0]) + " HTTP.VALUE: " + str(instantiating_nsi[1]))
  return jsonify(instantiating_nsi[0]), instantiating_nsi[1]

# INSTANTIATION UPDATE (internal endpoint to complete the previous, not public in the API page)
# INFORMATION: if changed, a line in nsi_manager.py within its function "createNSI" must have the same URL.
@app.route(API_ROOT+API_NSILCM+API_VERSION+API_NSI+'/<nsiId>/instantiation-change', methods=['POST'])
def update_slice_instantiation(nsiId):
  logging.info("SLICE_MAIN: received json tu update nsi: " + str(request.json))
  sliceUpdated = nsi_manager.update_instantiating_nsi(nsiId, request.json)

  #[0] error_message or valid_json, [1] status code
  return jsonify(sliceUpdated[0]), sliceUpdated[1]

# TERMINATES a NetSlice instance (NSI)
@app.route(API_ROOT+API_NSILCM+API_VERSION+API_NSI+'/<nsiId>/terminate', methods=['POST'])
def create_slice_terminate(nsiId):
  logging.info("SLICE_MAIN: received json from portal: " + str(request.json))
  
  # validates the fields with uuids (if they are right UUIDv4 format), 400 Bad request / 200 ok
  terminating_nsi = json_validator.validate_terminate_instantiation(request.json)
  
  if (terminating_nsi[1] == 200):
    terminating_nsi = nsi_manager.terminate_nsi(nsiId, request.json)  
  
  logging.info("SLICE_MAIN: HTTP.TEXT: " + str(terminating_nsi[0]) + " HTTP.VALUE: " + str(terminating_nsi[1]))
  return jsonify(terminating_nsi[0]), terminating_nsi[1]

# TERMINATE UPDATE (internal endpoint to complete the previous, not public in the API page)
# INFORMATION: if changed, a line in nsi_manager.py within its function "terminateNSI" must have the same URL.
@app.route(API_ROOT+API_NSILCM+API_VERSION+API_NSI+'/<nsiId>/terminate-change', methods=['POST'])
def update_slice_termination(nsiId):
  logging.info("SLICE_MAIN: received json to update a TERMINATING NSI: " + str(request.json))
  sliceUpdated = nsi_manager.update_terminating_nsi(nsiId, request.json)

  #[0] error_message or valid_json, [1] status code
  return jsonify(sliceUpdated[0]), sliceUpdated[1]

# GETS ALL the NetSlice instances (NSI) information
@app.route(API_ROOT+API_NSILCM+API_VERSION+API_NSI, methods=['GET'])
def get_slice_instances():
  allNSI = nsi_manager.get_all_nsi()

  return jsonify(allNSI[0]), allNSI[1]

# GETS a SPECIFIC NetSlice instances (NSI) information
@app.route(API_ROOT+API_NSILCM+API_VERSION+API_NSI+'/<nsiId>', methods=['GET'])
def get_slice_instance(nsiId):
  returnedNSI = nsi_manager.get_nsi(nsiId)

  return jsonify(returnedNSI[0]), returnedNSI[1]

# DELETEs from the ddbb the NetSlice Instance (NSI) record object
@app.route(API_ROOT+API_NSILCM+API_VERSION+API_NSI+'/<nsiId>', methods=['DELETE'])
def delete_slice_instance(nsiId):
  deleted_NSIid = nsi_manager.remove_nsi(nsiId)
  logging.info("SLICE_MAIN: Delete NSI with id: " + str(nsiId))
  
  if deleted_NSIid == 403:
    returnMessage = "Not possible to delete, the NSI is either in use or still being processed."
  else:
    returnMessage = "NSI with ID:" + str(nsiId) + "deleted from repositories."
  return jsonify(returnMessage)



################## TEMPORAL FUNCTIONS ################
# CREATES/INSTANTIATES a network
@app.route(API_ROOT+API_NSILCM+API_VERSION+API_NSI+'/network', methods=['POST'])
def create_network():
  logging.info("SLICE_MAIN: Creating networks: " + str(request.json))
  # calls the mapper to sent the networks creation requests to the GTK (and this to the IA)
  networks_data = request.json
  nets_creation_response = mapper.create_vim_network(networks_data)

  logging.info("SLICE_MAIN: Network Creation response: " + str(nets_creation_response))

  return jsonify(nets_creation_response)

@app.route(API_ROOT+API_NSILCM+API_VERSION+API_NSI+'/network', methods=['DELETE'])
def remove_network():
  logging.info("SLICE_MAIN: Removing networks: " + str(request.json))
  # calls the mapper to sent the networks creation requests to the GTK (and this to the IA)
  networks_data = request.json
  nets_removal_response = mapper.delete_vim_network(networks_data)

  logging.info("SLICE_MAIN: Network Removal response: " + str(nets_removal_response))

  return jsonify(nets_removal_response)


########################################### MAIN SERVER FUNCTION ############################################
if __name__ == '__main__':
  # READ CONFIG
  conf_parser = argparse.ArgumentParser( description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, add_help=True )
  conf_parser.add_argument("-c", "--conf_file", help="Specify config file", metavar="FILE", default='config.cfg')
  args, remaining_argv = conf_parser.parse_known_args()
  config = ConfigParser()
  config.read(args.conf_file)
  db.settings = config

  # PREPARE IA/MQRabbit Connection Thread
  #slicer_2_ia = slicer2ia.slicewrapper()

  # RUN MAIN SERVER THREAD
  app.run(debug=True, host='0.0.0.0', port=os.environ.get("SLICE_MGR_PORT"))
