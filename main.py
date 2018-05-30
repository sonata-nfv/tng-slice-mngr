#!/usr/bin/python

from flask import Flask, request, jsonify
import os, sys, logging, json, argparse 
from configparser import ConfigParser

import slice_lifecycle_mgr.nst_manager as nst_manager
import slice_lifecycle_mgr.nsi_manager as nsi_manager
import slice2ns_mapper.mapper as mapper
from database import database as db

app = Flask(__name__)

API_VERSION="v1"
API_ROOT="/api"
API_NST="/nst"
API_NSILCM="/nsilcm"
API_NSI="/nsi"

########################################## NETWORK SERVICES Actions #########################################
#asks all the available NetService Descriptors to the Sonata SP
@app.route('/api/services', methods=['GET'])
def getAllNetServ():
    ServDict = mapper.getListNetServices()
    logging.info('Returning all network services')
    return jsonify(ServDict), 200


######################################### NETSLICE TEMPLATE Actions #########################################
#creates a NetSlice template(NST)
@app.route(API_ROOT+API_NST+API_VERSION+'/descriptors', methods=['POST'])
def postNST():
    receivedNSTd = request.json
    new_NST = nst_manager.createNST(receivedNSTd)
    logging.info('NST created')
    return jsonify(new_NST), 201

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
def deleteNST(nstId):
    deleted_NSTid = nst_manager.deleteNST(nstId)
    if deleted_NSTid == 403:
      returnMessage = "Not possible to delete, there are NSInstances using this NSTemplate"
      logging.info(returnMessage)
      return jsonify(returnMessage), 403
    else:
      returnMessage = "The NST was deleted successfully."
      logging.info(returnMessage)
      return jsonify(returnMessage), 204


######################################### NETSLICE INSTANCE Actions #########################################
#creates and instantiates a NetSlice instance (NSI)
@app.route(API_ROOT+API_NSILCM+API_VERSION+API_NSI, methods=['POST'])
def postNSIinstantiation():
    new_NSI = request.json
    instantiatedNSI = nsi_manager.createNSI(new_NSI)
    logging.info('NSI Created and Instantiated')
    return jsonify(instantiatedNSI), 201

#terminates a NetSlice instance (NSI)
@app.route(API_ROOT+API_NSILCM+API_VERSION+API_NSI+'/<nsiId>/terminate', methods=['POST'])
def postNSItermination(nsiId):
    receivedTerminOrder = request.json
    terminateNSI = nsi_manager.terminateNSI(nsiId, receivedTerminOrder)
    logging.info('NSI Terminated')
    return jsonify(terminateNSI), 200

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
    conf_parser.add_argument("-c", "--conf_file",
                             help="Specify config file", metavar="FILE", default='config.cfg')
    args, remaining_argv = conf_parser.parse_known_args()
    config = ConfigParser()
    config.read(args.conf_file)
    db.settings = config
    
    #RUN SERVER
    app.run(debug=True, host='0.0.0.0', port=db.settings.getint("SLICE_MGR","SLICE_MGR_PORT"))
