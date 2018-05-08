#!/usr/bin/python

import os, sys, logging, datetime, uuid, time
import dateutil.parser

import objects.nsi_content as nsi
import slice2ns_mapper.mapper as mapper
import slice_lifecycle_mgr.nsi_manager2repo as nsi_repo
import database.database as db

def check_requests_status(token, requestsID_list):
    counter=0
    for resquestID_item in requestsID_list:
      getRequest_response = mapper.getRequestedNetServInstance(token, resquestID_item)     
      if(getRequest_response['status'] == 'READY'):
        counter=counter+1
    
    if (counter == len(requestsID_list)):
      return True
    else:
      return False

def instantiateNSI(nsi_jsondata):
    logging.info("CREATING A NEW NSI")
    
    #Generates a RANDOM (uuid4) UUID for this NSI
    uuident = uuid.uuid4()
    nsi_uuid = str(uuident)
    
    #creates NSI with the received information
    NSI = nsi.nsi_content()
    NSI.nsiId = nsi_uuid
    NSI.nsiName = nsi_jsondata['nsiName']
    NSI.nsiDescription = nsi_jsondata['nsiDescription']
    NSI.nstId = nsi_jsondata['nstId']
    #NSI.nstInfoId = nsi_jsondata['nstInfoId']
    #NSI.flavorId = nsi_jsondata['flavorId']
    #NSI.sapInfo = nsi_jsondata['sapInfo']
    NSI.nsiState = "INSTANTIATED"
    NSI.instantiateTime = str(datetime.datetime.now().isoformat())
      
    #instantiates required NetServices by sending requests to Sonata SP
    NST = db.nst_dict.get(NSI.nstId)  #TODO: substitute this db for the catalogue connection (GET)
    token = mapper.create_sonata_session()
    requestsID_list = []
    
    for uuidNetServ_item in NST.nstNsdIds:
      instantiation_response = mapper.net_serv_instantiate(token, uuidNetServ_item)
      requestsID_list.append(instantiation_response['id'])
    
    #checks if all instantiations in Sonata SP are READY to store NSI object
    allInstantiationsReady = False
    while (allInstantiationsReady == False):
      allInstantiationsReady = check_requests_status(token, requestsID_list)
      time.sleep(5)
    
    for request_uuid_item in requestsID_list:
      instantiation_response = mapper.getRequestedNetServInstance(token, request_uuid_item)
      NSI.netServInstance_Uuid.append(instantiation_response['service_instance_uuid'])
      
    #TODO: sends the NSI object information to the repository --> POST /records/nsir/ns-instances
    #db.nsi_dict[NSI.nsiId] = NSI
    NSI_string = vars(NSI)
    repo_response = nsi_repo.safe_nsi(NSI_string)

    #update nstUsageState parameter
    if NST.nstUsageState == "NOT_IN_USE":
      NST.nstUsageState = "IN_USE"
      db.nst_dict[NST.nstId] = NST  #TODO: substitute this db for the catalogue connection (PUT)
      
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
          token = mapper.create_sonata_session()
          
          #sends the requests to terminate all NetServiceInstances belonging to the NetSlice we are terminating
          for ServInstanceUuid_item in NSI.netServInstance_Uuid:
            termination = mapper.net_serv_terminate(token, ServInstanceUuid_item)
          
          #updates the NetSliceInstantiation information
          NSI.nsiState = "TERMINATE"
          
          #TODO: improve delete process to be done when the time defined in 'terminateTime' comes
          del db.nsi_dict[nsiId]
          return (vars(NSI))
        else:
          return "NSI is still instantiated: it was not possible to change its state."
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