#!/usr/bin/python

import os, sys, logging, datetime, uuid, time, json
import dateutil.parser

import objects.nsi_content as nsi
import slice2ns_mapper.mapper as mapper
import slice_lifecycle_mgr.nsi_manager2repo as nsi_repo
import database.database as db

def check_requests_status(requestsID_list):
    counter=0
    for resquestID_item in requestsID_list:
      getRequest_response = mapper.getRequestedNetServInstance(resquestID_item)  
      if(getRequest_response['status'] == 'READY'):
        counter=counter+1
    
    if (counter == len(requestsID_list)):
      return True
    else:
      return False

def instantiateNSI(nsi_jsondata):
    logging.info("NSI_MNGR: Creating a new NSI")
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
    requestsID_list = []   
    for uuidNetServ_item in NST.nstNsdIds:
      instantiation_response = mapper.net_serv_instantiate(uuidNetServ_item)
      requestsID_list.append(instantiation_response['id'])
    
    #checks if all instantiations in Sonata SP are READY to store NSI object
    allInstantiationsReady = False
    while (allInstantiationsReady == False):
      allInstantiationsReady = check_requests_status(requestsID_list)
      #time.sleep(5)
    
    for request_uuid_item in requestsID_list:
      instantiation_response = mapper.getRequestedNetServInstance(request_uuid_item)
      NSI.netServInstance_Uuid.append(instantiation_response['service_instance_uuid'])
      
    NSI_string = vars(NSI)
    nsirepo_jsonresponse = nsi_repo.safe_nsi(NSI_string)

    #update nstUsageState parameter
    if NST.usageState == "NOT_IN_USE":
      NST.usageState = "IN_USE"
      db.nst_dict[NST.id] = NST                                        #TODO: substitute this db for the catalogue connection (PUT)
      
    return nsirepo_jsonresponse

def terminateNSI(nsiId, TerminOrder):
    logging.info("NSI_MNGR: Terminate NSI with id: " +str(nsiId))
    time.sleep(.2)
    #NSI = db.nsi_dict.get(nsiId)                                       #TODO: substitute with the repositories command (GET)
    repo_jsonresponse = nsi_repo.get_saved_nsi(nsiId)
    
    #prepares the NSI object to manage with the info coming from repositories
    NSI = nsi.nsi_content()
    NSI.id = repo_jsonresponse['uuid']
    NSI.name = repo_jsonresponse['name']
    NSI.description = repo_jsonresponse['description']
    NSI.nstId = repo_jsonresponse['nstId']
    NSI.vendor = repo_jsonresponse['vendor']
    NSI.nstInfoId = repo_jsonresponse['nstInfoId']
    NSI.flavorId = repo_jsonresponse['flavorId']
    NSI.sapInfo = repo_jsonresponse['sapInfo']
    NSI.nsiState = repo_jsonresponse['nsiState']  
    netServInsID_array = repo_jsonresponse['netServInstance_Uuid']
    for NetServInsID_item in netServInsID_array:
      NSI.netServInstance_Uuid.append(NetServInsID_item)
    NSI.instantiateTime = repo_jsonresponse['instantiateTime']
    NSI.terminateTime = repo_jsonresponse['terminateTime']
    NSI.scaleTime = repo_jsonresponse['scaleTime']
    NSI.updateTime = repo_jsonresponse['updateTime']
    
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
        #termination requests to all NetServiceInstances belonging to the NetSlice
        for ServInstanceUuid_item in NSI.netServInstance_Uuid:
          termination = mapper.net_serv_terminate(ServInstanceUuid_item) #TODO: validate all related NetService instances are terminated
        
        logging.info("NSI_MNGR: All NetService Instances stopped.")
        time.sleep(.2)
      
      repo_response = nsi_repo.delete_nsi(nsiId)
      logging.info("NSI_MNGR: NSI deleted from repositories.")
      time.sleep(.2)
      
      NSI.nsiState = "TERMINATE"
      return (vars(NSI))
    elif instan_time < termin_time:                                     #TODO: manage future termination orders
      NSI.terminateTime = termin_time
      NSI.nsiState = "TERMINATE"
      return (vars(NSI))  
    else:
      return ("Please specify a correct termination: 0 to terminate inmediately or a time value later than: " + NSI.instantiateTime+ ", to terminate in the future.")

def getNSI(nsiId):
    logging.info("NSI_MNGR: Retrieving NSI with id: " +str(nsiId))
    repo_jsonresponse = nsi_repo.get_saved_nsi(nsiId)

    return repo_jsonresponse

def getAllNsi():
    logging.info("NSI_MNGR: Retrieve all existing NSIs")
    repo_jsonresponse = nsi_repo.getAll_saved_nsi()
    
    return repo_jsonresponse