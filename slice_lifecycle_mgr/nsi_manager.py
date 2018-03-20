#!/usr/bin/python

import os, sys, logging, datetime, uuid
import dateutil.parser

import objects.nsi_content as nsi
import database.database as db



def createNSI(jsondata):
    logging.info("CREATING A NEW NSI")
    
    #Generate the UUID for this NSI
    uuident = uuid.uuid4()
    nsi_uuid = str(uuident)
    
    #Assigns the received information to the right parameter
    NSI = nsi.nsi_content()
    NSI.id = nsi_uuid
    NSI.nsiName = jsondata['nsiName']
    NSI.nsiDescription = jsondata['nsiDescription']
    NSI.nstId = jsondata['nstId']
    NSI.nstInfoId = jsondata['nstInfoId']
    NSI.flavorId = jsondata['flavorId']
    NSI.sapInfo = jsondata['sapInfo']
    NSI.nsiState = jsondata['nsiState']

    db.nsi_dict[NSI.id] = NSI
    return NSI.id


def instantiateNSI(nsiId):
    logging.info("INSTANTIATING A NSI")
    NSI = db.nsi_dict.get(nsiId)
    if NSI.nsiState == "NOT_INSTANTIATED":
      
      #do all the necessary processes (call functions to SONATA)
      
      NSI.nsiState = "INSTANTIATED"
      instantiateTime = datetime.datetime.now()
      NSI.instantiateTime = str(instantiateTime.isoformat())
      
      return vars(NSI)
    else:
      return "NSI not instantiated"
      
def terminateNSI(nsiId, terminationRx):
    logging.info("TERMINATING A NSI")
    NSI = db.nsi_dict.get(nsiId)

    #Parsing from string ISO to datetime format to compare values
    instan_time = dateutil.parser.parse(NSI.instantiateTime)
    termin_time = dateutil.parser.parse(terminationRx['terminateTime'])

    if instan_time < termin_time:
        NSI.terminateTime = terminationRx['terminateTime']
        if NSI.nsiState == "INSTANTIATED":

            # do all the necessary processes (call functions to SONATA)

            NSI.nsiState = "NOT_INSTANTIATED"
            
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