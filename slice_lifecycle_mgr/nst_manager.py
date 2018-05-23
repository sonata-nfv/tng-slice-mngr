#!/usr/bin/python

import os, sys, logging, uuid
import objects.nst_content as nst
import database.database as db


def createNST(jsondata):
    logging.info("NST_MNGR: Ceating a new NST")
    
    #Generate the UUID for this NSI
    uuident = uuid.uuid4()
    nst_uuid = str(uuident)
    
    #Assigns the received information to the right parameter
    NST = nst.nst_content()
    NST.id = nst_uuid
    NST.name = jsondata['name']
    NST.version = jsondata['version']
    NST.author = jsondata['author']
    NST.vendor = jsondata ['vendor']
    
    nstNsdIds_array = jsondata['nstNsdIds']
    for nsiId_item in nstNsdIds_array:
        NST.nstNsdIds.append(nsiId_item['NsdId'])
    
    NST.onboardingState = "ENABLED"
    NST.operationalState = "ENABLED"
    NST.usageState = "NOT_IN_USE"
    #NST.notificationTypes = jsondata['notificationTypes']          #TODO: where does it come from??
    #NST.userDefinedData = jsondata['userDefinedData']              #TODO: where does it come from??
        
    db.nst_dict[NST.id] = NST  
    return vars(NST)

def getNST(nstId):                                                  #TODO: use the CATALOGUE command
    logging.info("NST_MNGR: Return NST with id: " + str(nstId))
    NST = db.nst_dict.get(nstId)
    return (vars(NST))
  
def getAllNst():                                                    #TODO: use the CATALOGUE command
    logging.info("NST_MNGR: Return all NSTs")
    nst_list = []
    for nst_item in db.nst_dict:
        NST = db.nst_dict.get(nst_item)
        nst_string = vars(NST)
        nst_list.append(nst_string)
    return nst_list 
    
def deleteNST(nstId):                                               #TODO: use the CATALOGUE command
    logging.info("NST_MNGR: Delete NST with id: " + str(nstId))
    NST = db.nst_dict.get(nstId)
    if NST.usageState == "NOT_IN_USE":
      logging.info("Deleting Network Slice Template")
      del db.nst_dict[nstId]
      return nstId
    else:
      return 403