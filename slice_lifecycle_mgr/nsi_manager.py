#!/usr/bin/python

import os, sys, logging, datetime, uuid
import dateutil.parser

import objects.nsi_content as nsi
import slice2ns_mapper.mapper as mapper
import database.database as db



def createNSI(jsondata):
    logging.info("CREATING A NEW NSI")
    
    #Generates a RANDOM (uuid4) UUID for this NSI
    uuident = uuid.uuid4()
    nsi_uuid = str(uuident)
    
    #Assigns the received information to the right parameter
    NSI = nsi.nsi_content()
    NSI.nsiId = nsi_uuid
    NSI.nsiName = jsondata['nsiName']
    NSI.nsiDescription = jsondata['nsiDescription']
    NSI.nstId = jsondata['nstId']
    #NSI.nstInfoId = jsondata['nstInfoId']
    #NSI.flavorId = jsondata['flavorId']
    #NSI.sapInfo = jsondata['sapInfo']
    NSI.nsiState = "NOT_INSTANTIATED"

    db.nsi_dict[NSI.nsiId] = NSI
    return NSI.nsiId


def instantiateNSI(nsiId):
    logging.info("INSTANTIATING A NSI")  

    #updates the NetSlice Instantiation information
    NSI = db.nsi_dict.get(nsiId)
    instantiateTime = datetime.datetime.now()
    NSI.instantiateTime = str(instantiateTime.isoformat())
    if NSI.nsiState == "NOT_INSTANTIATED":
      NSI.nsiState = "INSTANTIATED"
    
    #requests session token for sonata
    token = mapper.create_sonata_session()
    
    #sends NetServices requests to SonataSP
    NST = db.nst_dict.get(NSI.nstId)
    for uuidNetServ_item in NST.nstNsdIds:
      instantiation = mapper.net_serv_instantiate(token, uuidNetServ_item)
    
    #updates nstUsageState parameter
    if NST.nstUsageState == "NOT_USED":
      NST.nstUsageState = "IN_USE"
      db.nst_dict[NST.nstId] = NST
      
    return vars(NSI)
    
      
def terminateNSI(nsiId, TerminOrder):
    logging.info("TERMINATING A NSI")
    NSI = db.nsi_dict.get(nsiId)
    
    #Parsing from string ISO to datetime format to compare values
    instan_time = dateutil.parser.parse(NSI.instantiateTime)
    termin_time = dateutil.parser.parse(TerminOrder['terminateTime'])

    if instan_time < termin_time:
        NSI.terminateTime = TerminOrder['terminateTime']
        if NSI.nsiState == "INSTANTIATED":
          #requests session token for sonata
          #token = mapper.create_sonata_session()
        
          #sends the requests to terminate a NetServiceInstance in sonata
          #termination = mapper.net_serv_terminate(token, nsiId)     
          
          #updates the NetSliceInstantiation information
          NSI.nsiState = "TERMINATE"
            
          return (vars(NSI))
        else:
          return "NSI is still instantiated: it was not possible to change the state."
    else:
      return ("Please specify a correct termination time bigger than: " + NSI.instantiateTime)

def getNSI(nsiId):
    logging.info("RETRIEVING A NSI")
    NSI = db.nsi_dict.get(nsiId)

    return (vars(NSI))


def getAllNsi():
    logging.info("RETRIEVING ALL EXISTING NSIs")
    nsi_list = []
    for nsi_item in db.nsi_dict:
        NSI = db.nsi_dict.get(nsi_item)
        nsi_string = vars(NSI)
        nsi_list.append(nsi_string)
    
    return (nsi_list)


def deleteNSI(nsiId):
    logging.info("DELETING A NSI")
    logging.info("Deleting Network Slice Instantiation")
    del db.nst_dict[nsiId]
    
    return (nsiId)