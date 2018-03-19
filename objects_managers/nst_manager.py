#!/usr/bin/python

import os, sys, logging
import objects.nst_content as nst
import database.database as db


def createNST(jsondata):
    logging.info("CREATING A NEW NST")
    # print(json.dumps(jsondata, indent=4, sort_keys=True))

    NST = nst.nst_content()
    NST.id = jsondata['id']
    NST.nstId = jsondata['nstId']
    NST.nstName = jsondata['nstName']
    NST.nstVersion = jsondata['nstVersion']
    NST.nstDesigner = jsondata['nstDesigner']
    NST.nstInvariantId = jsondata['nstInvariantId']

    nstNsdIds_array = jsondata['nstNsdIds']
    for item in nstNsdIds_array:
        NST.nstNsdIds.append(item['nstNsdId'])

    NST.nstOnboardingState = jsondata['nstOnboardingState']
    NST.nstOperationalState = jsondata['nstOperationalState']
    NST.nstUsageState = jsondata['nstUsageState']
    NST.notificationTypes = jsondata['notificationTypes']
    NST.userDefinedData = jsondata['userDefinedData']
    
    db.nst_dict[jsondata['id']] = NST
    return NST.nstId


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
    logging.info("Deleting Network Slice Template")
    del db.nst_dict[nstId]
    return nstId
    