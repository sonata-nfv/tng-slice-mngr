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

from flask import Flask, request, jsonify
import os, sys, logging, json, argparse 
from configparser import ConfigParser

import slice_lifecycle_mgr.nst_manager as nst_manager
import slice_lifecycle_mgr.nsi_manager as nsi_manager
import slice_lifecycle_mgr.validate_incoming_json as json_validator
import slice2ns_mapper.mapper as mapper
from database import database as db

app = Flask(__name__)

#/api/nst/v1/
#/api/nsilcm/v1/nsi
API_ROOT="/api"
API_NST="/nst"
API_VERSION="/v1"
API_NSILCM="/nsilcm"
API_NSI="/nsi"



############################################# NETWORK SLICE PING ############################################
#function to validate if the slice-docker is active
@app.route('/pings', methods=['GET'])
def getPings():
    ping_response  = {'alive_since': '2018-07-18 10:00:00 UTC'}
    
    return jsonify(ping_response), 200


########################################## NETWORK SERVICES Actions #########################################
#asks all the available NetService Descriptors to the Sonata SP
@app.route('/api/services', methods=['GET'])
def getAllNetServ():
    ServDict = mapper.getListNetServices()
    logging.info('Returning all network services')
    
    return jsonify(ServDict), 200


######################################### NETSLICE TEMPLATE Actions #########################################
@app.route(API_ROOT+API_NST+API_VERSION+'/descriptors', methods=['OPTIONS'])
def optionsAllNST():
   
   return "Allow: OPTIONS, GET, HEAD, POST", 200

@app.route(API_ROOT+API_NST+API_VERSION+'/descriptors/<nstId>', methods=['OPTIONS']) 
def optionsOneNST(nstId):
   
   return "Allow: OPTIONS, GET, HEAD, POST", 200

#creates a NetSlice template(NST)
@app.route(API_ROOT+API_NST+API_VERSION+'/descriptors', methods=['POST']) 
def NST_creation():
    receivedNSTd = request.json
    logging.info("SLICE_MAIN: received json from portal: " + str(receivedNSTd))
    # validates the fields with uuids (if they are right UUIDv4 format), 400 Bad request / 201 ok
    validationResponse = json_validator.validateCreateTemplate(receivedNSTd)
    if (validationResponse[1] == 201):
      new_NST = nst_manager.createNST(receivedNSTd)
      logging.info('NST created')
      
      return jsonify(new_NST), 201
    
    else:
      
      return jsonify(validationResponse[0]), validationResponse[1]            

#asks for all the NetSlice Templates (NST) information
@app.route(API_ROOT+API_NST+API_VERSION+'/descriptors', methods=['GET'])
def getAllNST():
    listNST = nst_manager.getAllNst()    
    logging.info('Returning all NST')
    
    return jsonify(listNST), 200

#asks for a specific NetSlice Template (NST) information
@app.route(API_ROOT+API_NST+API_VERSION+'/descriptors/<nstId>', methods=['GET'])
def getNST(nstId):
    returnedNST = nst_manager.getNST(nstId)   
    logging.info('Returning the desired NST')
   
    return jsonify(returnedNST), 200

#deletes a NetSlice Template
@app.route(API_ROOT+API_NST+API_VERSION+'/descriptors/<nstId>', methods=['DELETE'])
def delete_NST(nstId):
    deleted_NSTid = nst_manager.deleteNST(nstId)
    if deleted_NSTid == 403:
      returnMessage = "Not possible to delete, there are NSInstances using this NSTemplate"
      logging.info(returnMessage)
      
      return jsonify(returnMessage), 403
    
    else: 
      logging.info("The NST was deleted successfully.")
      
      return 204


######################################### NETSLICE INSTANCE Actions #########################################
#CREATES/INSTANTIATES a NetSlice instance (NSI)
@app.route(API_ROOT+API_NSILCM+API_VERSION+API_NSI, methods=['POST'])
def NSI_instantiation():
    new_NSI = request.json
    logging.info("SLICE_MAIN: received json from portal: " + str(new_NSI))
    # validates the fields with uuids (if they are right UUIDv4 format), 400 Bad request / 201 ok
    validationResponse = json_validator.validateCreateInstantiation(new_NSI)
    if (validationResponse[1] == 201):
      logging.debug(new_NSI)
      instantiatedNSI = nsi_manager.createNSI(new_NSI)
      logging.info('NSI Created and Instantiated')
      
      return jsonify(instantiatedNSI), 201
    
    else:
      
      return jsonify(validationResponse[0]), validationResponse[1]

#INSTANTIATION UPDATE
#INFORMATION: if this endpoint is changed, there's a line in nsi_manager.py within its function "createNSI" that must have the same URL.
@app.route(API_ROOT+API_NSILCM+API_VERSION+API_NSI+'/<nsiId>/instantiation-change', methods=['POST'])
def updateSliceInstance(nsiId):
    updatedService = request.json
    logging.info("SLICE_MAIN: received json to update an instantiating NSI: " + str(updatedService))
    sliceUpdated = nsi_manager.updateInstantiatingNSI(nsiId, updatedService)
      
    return (sliceUpdated[0], sliceUpdated[1]) #[0] - error_message or valid_json, [1] - status code

#TERMINATES a NetSlice instance (NSI)
@app.route(API_ROOT+API_NSILCM+API_VERSION+API_NSI+'/<nsiId>/terminate', methods=['POST'])
def NSI_termination(nsiId):
    terminate_json = request.json
    logging.info("SLICE_MAIN: received json from portal: " + str(terminate_json))
    # validates the fields with uuids (if they are right UUIDv4 format), 400 Bad request / 201 ok
    validationResponse = json_validator.validateTerminateInstantiation(terminate_json)
    if (validationResponse[1] == 200):
      terminateNSI = nsi_manager.terminateNSI(nsiId, terminate_json)
      logging.info('NSI Terminated')
      
      return jsonify(terminateNSI), 200
   
    else:
      
      return jsonify(validationResponse[0]), validationResponse[1]

#TERMINATE UPDATE
#INFORMATION: if this endpoint is changed, there's a line in nsi_manager.py within its function "terminateNSI" that must have the same URL.
@app.route(API_ROOT+API_NSILCM+API_VERSION+API_NSI+'/<nsiId>/terminate-change', methods=['POST'])
def updateSliceTerminate(nsiId):
    updatedService = request.json
    logging.info("SLICE_MAIN: received json to update a terminating NSI: " + str(updatedService))
    sliceUpdated = nsi_manager.updateTerminatingNSI(nsiId, updatedService)

    # [0] - error_message or valid_json, [1] - status code  
    return (sliceUpdated[0], sliceUpdated[1])

#asks for all the NetSlice instances (NSI) information
@app.route(API_ROOT+API_NSILCM+API_VERSION+API_NSI, methods=['GET'])
def getALLNSI():
    allNSI = nsi_manager.getAllNsi()
    logging.info('Returning all NSI')
    
    return jsonify(allNSI), 200

#asks for a specific NetSlice instances (NSI) information
@app.route(API_ROOT+API_NSILCM+API_VERSION+API_NSI+'/<nsiId>', methods=['GET'])
def getNSI(nsiId):
    returnedNSI = nsi_manager.getNSI(nsiId)
    logging.info('Returning the NSI with id:' +str(nsiId))
    
    return jsonify(returnedNSI), 200


#MAIN FUNCTION OF THE SERVER
if __name__ == '__main__':
    #READ CONFIG
    conf_parser = argparse.ArgumentParser( description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, add_help=True )
    conf_parser.add_argument("-c", "--conf_file", help="Specify config file", metavar="FILE", default='config.cfg')
    args, remaining_argv = conf_parser.parse_known_args()
    config = ConfigParser()
    config.read(args.conf_file)
    db.settings = config
    
    #RUN SERVER
    app.run(debug=True, host='0.0.0.0', port=os.environ.get("SLICE_MGR_PORT"))
