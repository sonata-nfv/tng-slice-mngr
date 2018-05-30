#!/usr/bin/python

import os, sys, logging, uuid
import objects.nst_content as nst
import slice_lifecycle_mgr.nst_manager2catalogue as nst_catalogue
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
        
    db.nst_dict[NST.id] = NST                                       #TODO: use the CATALOGUE command
    #NST_string  =vars(NST)
    #nstcatalogue_jsonresponse = nst_catalogue.safe_nst(NST_string)
    return vars(NST)
    #return nstcatalogue_jsonresponse

def getAllNst():
    logging.info("NST_MNGR: Retrieving all existing NSTs")
    nst_list = []
    for nst_item in db.nst_dict:
        NST = db.nst_dict.get(nst_item)                             #TODO: use the CATALOGUE command
        nst_string = vars(NST)
        nst_list.append(nst_string)  
    #nstcatalogue_jsonresponse = nst_catalogue.getAll_saved_nst()
    return nst_list
    #return nstcatalogue_jsonresponse

def getNST(nstId):                                                  
    logging.info("NST_MNGR: Retrieving NST with id: " + str(nstId))
    NST = db.nst_dict.get(nstId)                                    #TODO: use the CATALOGUE command
    #nstcatalogue_jsonresponse = nst_catalogue.get_saved_nst(nstId)
    return (vars(NST))
    #return nstcatalogue_jsonresponse
    
def updateNST(nstId, NST_string):
    logging.info("NST_MNGR: Updating NST with id: " +str(nstId))
    nstcatalogue_jsonresponse = nst_catalogue.update_nst(update_NST, nstId)
    return nstcatalogue_jsonresponse

def deleteNST(nstId):
    logging.info("NST_MNGR: Delete NST with id: " + str(nstId))
    NST = db.nst_dict.get(nstId)                                    #TODO: use the CATALOGUE command
    #nstcatalogue_jsonresponse = nst_catalogue.get_saved_nst(nstId)
    #if (nstcatalogue_jsonresponse["usageState"] == "NOT_IN_USE"):
    if NST.usageState == "NOT_IN_USE":
      del db.nst_dict[nstId]                                        #TODO: use the CATALOGUE command
      #nstcatalogue_jsonresponse = nst_catalogue.delete_nsi(nstId)
      return nstId
      #return nstcatalogue_jsonresponse
    else:
      return 403