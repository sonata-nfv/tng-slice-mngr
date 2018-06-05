#!/usr/bin/python

import os, sys, logging, uuid
import objects.nst_content as nst

import slice_lifecycle_mgr.nst_manager2catalogue as nst_catalogue
import database.database as db

#Creates a NST and sends it to catalogues
def createNST(jsondata):
    logging.info("NST_MNGR: Ceating a new NST")
    NST = nst.nst_content()
    #NST.id = nst_uuid                            #given by the catalogues
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
    NST_string = vars(NST)
    nstcatalogue_jsonresponse = nst_catalogue.safe_nst(NST_string)
    return nstcatalogue_jsonresponse

#Returns the information of all the NST in catalogues
def getAllNst():
    logging.info("NST_MNGR: Retrieving all existing NSTs")
    nstcatalogue_jsonresponse = nst_catalogue.getAll_saved_nst()
    return nstcatalogue_jsonresponse

#Returns the information of a selected NST in catalogues
def getNST(nstId):                                                  
    logging.info("NST_MNGR: Retrieving NST with id: " + str(nstId))
    nstcatalogue_jsonresponse = nst_catalogue.get_saved_nst(nstId)
    return nstcatalogue_jsonresponse

#Updates the information of a selected NST in catalogues  
def updateNST(nstId, NST_string):
    logging.info("NST_MNGR: Updating NST with id: " +str(nstId))
    nstcatalogue_jsonresponse = nst_catalogue.update_nst(update_NST, nstId)
    return nstcatalogue_jsonresponse

#Deletes a NST kept in catalogues
def deleteNST(nstId):
    logging.info("NST_MNGR: Delete NST with id: " + str(nstId))
    nstcatalogue_jsonresponse = nst_catalogue.get_saved_nst(nstId)
    if (nstcatalogue_jsonresponse['nstd']["usageState"] == "NOT_IN_USE"):  
      nstcatalogue_jsonresponse = nst_catalogue.delete_nsi(nstId)
      return nstcatalogue_jsonresponse
      
    else:
      return 403