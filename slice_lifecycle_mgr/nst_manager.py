#!/usr/bin/python

import os, sys, logging, uuid
import objects.nst_content as nst
import database.database as db


def createNST(jsondata):
    logging.info("CREATING A NEW NST")
    
    #Generate the UUID for this NSI
    uuident = uuid.uuid4()
    nst_uuid = str(uuident)
    
    #Assigns the received information to the right parameter
    NST = nst.nst_content()
    NST.nstId = nst_uuid
    NST.nstName = jsondata['nstName']
    NST.nstVersion = jsondata['nstVersion']
    NST.nstDesigner = jsondata['nstDesigner']
    #NST.nstInvariantId = jsondata['nstInvariantId']
    
    nstNsdIds_array = jsondata['nstNsdIds']
    for nsiId_item in nstNsdIds_array:
        NST.nstNsdIds.append(nsiId_item['nstNsdId'])
    
    NST.nstOnboardingState = "ENABLED"
    NST.nstOperationalState = "ENABLED"
    NST.nstUsageState = "NOT_IN_USE"
    #NST.notificationTypes = jsondata['notificationTypes']
    #NST.userDefinedData = jsondata['userDefinedData']      
    
    db.nst_dict[NST.nstId] = NST  
    return vars(NST)

def getNST(nstId):
    NST = db.nst_dict.get(nstId)
    return (vars(NST))
  
def getAllNst():
    nst_list = []
    for nst_item in db.nst_dict:
        NST = db.nst_dict.get(nst_item)
        nst_string = vars(NST)
        nst_list.append(nst_string)
    return nst_list 
    
def deleteNST(nstId):
    NST = db.nst_dict.get(nstId)
    if NST.nstUsageState == "NOT_USED":
      logging.info("Deleting Network Slice Template")
      del db.nst_dict[nstId]
      return nstId
    else:
      return 403