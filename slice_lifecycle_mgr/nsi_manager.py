#!/usr/bin/python

import os, sys, logging, datetime, uuid, time
import dateutil.parser

import objects.nsi_content as nsi
import slice2ns_mapper.mapper as mapper
import slice_lifecycle_mgr.nsi_manager2repo as nsi_repo
import database.database as db

def check_requests_status(token, requestsID_list):
#def check_requests_status(requestsID_list):
    counter=0
    for resquestID_item in requestsID_list:
      getRequest_response = mapper.getRequestedNetServInstance(token, resquestID_item)
      #getRequest_response = mapper.getRequestedNetServInstance(resquestID_item)  
      if(getRequest_response['status'] == 'READY'):
        counter=counter+1
    
    if (counter == len(requestsID_list)):
      return True
    else:
      return False

def instantiateNSI(nsi_jsondata):
    logging.info("CREATING A NEW NSI")
    NST = db.nst_dict.get(nsi_jsondata['nstId'])                       #TODO: substitute this db for the catalogue connection (GET)
    
    #Generates a RANDOM (uuid4) UUID for this NSI
    uuident = uuid.uuid4()
    nsi_uuid = str(uuident)
    
    #creates NSI with the received information
    NSI = nsi.nsi_content()
    NSI.id = nsi_uuid
    NSI.name = nsi_jsondata['name']
    NSI.description = nsi_jsondata['description']
    NSI.nstId = nsi_jsondata['nstId']
    NSI.vendor = NST.getVendor()
    #NSI.nstInfoId = nsi_jsondata['nstInfoId']                         #TODO: where does it come from??
    #NSI.flavorId = nsi_jsondata['flavorId']                           #TODO: where does it come from??
    #NSI.sapInfo = nsi_jsondata['sapInfo']                             #TODO: where does it come from??
    NSI.nsiState = "INSTANTIATED"
    NSI.instantiateTime = str(datetime.datetime.now().isoformat())
      
    #instantiates required NetServices by sending requests to Sonata SP
    token = mapper.create_sonata_session()
    requestsID_list = []   
    for uuidNetServ_item in NST.nstNsdIds:
      instantiation_response = mapper.net_serv_instantiate(token, uuidNetServ_item)
      #instantiation_response = mapper.net_serv_instantiate(uuidNetServ_item)
      requestsID_list.append(instantiation_response['id'])
    
    #checks if all instantiations in Sonata SP are READY to store NSI object
    allInstantiationsReady = False
    while (allInstantiationsReady == False):
      allInstantiationsReady = check_requests_status(token, requestsID_list)
      #allInstantiationsReady = check_requests_status(requestsID_list)
      time.sleep(5)
    
    for request_uuid_item in requestsID_list:
      instantiation_response = mapper.getRequestedNetServInstance(token, request_uuid_item)
      #instantiation_response = mapper.getRequestedNetServInstance(request_uuid_item)
      NSI.netServInstance_Uuid.append(instantiation_response['service_instance_uuid'])
      
    #db.nsi_dict[NSI.id] = NSI                                          ########TODO: sends the NSI object information to the repository
    NSI_string = vars(NSI)
    nsirepo_jsonresponse = nsi_repo.safe_nsi(NSI_string)

    #update nstUsageState parameter
    if NST.usageState == "NOT_IN_USE":
      NST.usageState = "IN_USE"
      db.nst_dict[NST.id] = NST                                        #TODO: substitute this db for the catalogue connection (PUT)
      
    #return vars(NSI)
    return nsirepo_jsonresponse

def terminateNSI(nsiId, TerminOrder):
    logging.info("TERMINATING A NSI")
    NSI = db.nsi_dict.get(nsiId)                                       #TODO: substitute with the repositories command (GET)
    
    #prepares the datetime values to work with them
    instan_time = dateutil.parser.parse(NSI.instantiateTime)
    if TerminOrder['terminateTime'] == "0":
      termin_time = 0
    else:
      termin_time = dateutil.parser.parse(TerminOrder['terminateTime'])
    
    #depending on the termin_time executes one action or another
    if termin_time == 0:
      NSI.terminateTime = str(datetime.datetime.now().isoformat())
      if NSI.nsiState == "INSTANTIATED":
        #requests session token for sonata
        token = mapper.create_sonata_session()
        
        #sends the requests to terminate all NetServiceInstances belonging to the NetSlice we are terminating
        for ServInstanceUuid_item in NSI.netServInstance_Uuid:
          #termination = mapper.net_serv_terminate(ServInstanceUuid_item)
          termination = mapper.net_serv_terminate(token, ServInstanceUuid_item)
         
      NSI.nsiState = "TERMINATE"                                        #TODO: validate all related NetService instances are terminated
      return (vars(NSI))
    elif instan_time < termin_time:                                     #TODO: manage future termination orders
      NSI.terminateTime = termin_time
      return (vars(NSI))  
    else:
      return ("Please specify a correct termination: 0 to terminate inmediately or a time value later than " + NSI.instantiateTime+ "- to terminate in the future.")

def getNSI(nsiId):
    logging.info("RETRIEVING A NSI")
    #NSI = db.nsi_dict.get(nsiId)                                        ######TODO: substitute with the repositories command (GET)
    repo_jsonresponse = nsi_repo.get_saved_nsi(nsiId)

    #return (vars(NSI))
    return repo_jsonresponse

def getAllNsi():
    logging.info("RETRIEVING ALL EXISTING NSIs")
#    nsi_list = []
#    for nsi_item in db.nsi_dict:
#        NSI = db.nsi_dict.get(nsi_item)                                 #TODO: substitute with the repositories command (GET)
#        nsi_string = vars(NSI)
#        nsi_list.append(nsi_string)
    repo_jsonresponse = nsi_repo.getAll_saved_nsi()
    
    #return (nsi_list)
    return repo_jsonresponse