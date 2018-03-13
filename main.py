#!/usr/bin/python

from flask import Flask, request
import os, sys, logging, json

import objects_managers.nst_manager as nst_manager


app = Flask(__name__)

# ----- NETSLICE TEMPLATE Actions -----
@app.route('/nst/v1/descriptors', methods=['POST'])
def postNST():
    receivedNSTd = request.json
    new_NST = nst_manager.createNST(receivedNSTd)
    return ('New NST created into the database with id: ' + str(new_NST))

@app.route('/nst/v1/descriptors', methods=['GET'])
def getAllNST():
    allNST = nst_manager.getAllNst()
    jsonNSTList = json.dumps(allNST, indent=4, sort_keys=True)
    logging.info('Returning all NST')
    return (jsonNSTList)

@app.route('/nst/v1/descriptors/<int:nstId>', methods=['GET'])
def getNST(nstId):
    returnedNST = nst_manager.getNST(nstId)
    jsonNST = json.dumps(returnedNST, indent=4, sort_keys=True)
    logging.info('Returning the desired NST')
    return jsonNST

@app.route('/nst/v1/descriptors/<int:nstId>', methods=['DELETE'])
def deleteNST(nstId):
    deleted_NSTid = nst_manager.deleteNST(nstId)
    return ('Deletes the specified NST with id: ' +str(deleted_NSTid))


## ----- NETSLICE INSTANCE Actions -----
#@app.route('/nsi', methods=['POST'])
#def createNSI():
#  return 'Creating a new NSI!'
#
#@app.route('/nsi', methods=['GET'])
#def getNSIList():
#  return 'Returning the list of the current NSI!'
#
#@app.route('/nsi/<int:nsiId>', methods=['GET'])
#def getNSI(nsiId):
#  return 'Returning the information of a specific NSI'
#
#@app.route('/nsi/<int:nsiId>', methods=['DELETE'])
#def deleteNSI(nsiId):
#  #db.nsi_list.del[nsiId]
#  return 'Deletes the specifici NSI'
#
#@app.route('/nsi/<int:nsiId>/instantiate', methods=['POST'])
#def postNSIinstantiation(nsiId):
#  return 'Instantiates the specifici NSI'
#
#@app.route('/nsi/<int:nsiId>/terminate', methods=['POST'])
#def postNSItermination(nsiId):
#
#  return 'Terminates the specifici NSI: %d' % nsiId

if __name__ == '__main__':
  app.run(debug=True)
