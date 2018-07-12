#!/usr/bin/python

import os, sys, logging, datetime, uuid, time, json
import dateutil.parser

import objects.nsi_content as nsi
import slice2ns_mapper.mapper as mapper
import slice_lifecycle_mgr.nsi_manager2repo as nsi_repo
import slice_lifecycle_mgr.nst_manager2catalogue as nst_catalogue
import database.database as db

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("slicemngr:repo")
LOG.setLevel(logging.INFO)

##### CREATE NSI SECTION #####
#MAIN FUNCTION: createNSI(...)
#related functions: parseNetSliceInstance(), instantiateNetServices(), checkRequestsStatus()
def createNSI(nsi_jsondata):                                        #TODO: add and if condition for each response to acces the next one or return with the error
    LOG.info("NSI_MNGR: Creating a new NSI")
    nstId = nsi_jsondata['nstId']
    catalogue_response = nst_catalogue.get_saved_nst(nstId)
    logging.debug('catalogue_response '+str(catalogue_response))
    nst_json = catalogue_response['nstd']
        
    #creates NSI with the received information
    NSI = parseNewNSI(nst_json, nsi_jsondata)
      
    #instantiates required NetServices by sending requests to Sonata SP
    requestsUUID_list = instantiateNetServices(nst_json['nstNsdIds'])
    logging.debug('requestsID_list: '+str(requestsUUID_list))

    #checks if all instantiations in Sonata SP are READY to store NSI object
    allInstantiationsReady = "NEW"
    while (allInstantiationsReady == "NEW" or allInstantiationsReady == "INSTANTIATING"):
      allInstantiationsReady = checkRequestsStatus(requestsUUID_list)
      time.sleep(30)
    
    #with all Services instantiated, it gets their uuids and keeps them inside the NSI information.
    for request_uuid_item in requestsUUID_list:
      instantiation_response = mapper.getRequestedNetServInstance(request_uuid_item)
      NSI.netServInstance_Uuid.append(instantiation_response['instance_uuid'])

    #Updating the the usageState parameter of the slelected NST
    if (nst_json['usageState'] == "NOT_IN_USE"):  
      nstParameter2update = "usageState=IN_USE"
      updatedNST_jsonresponse = nst_catalogue.update_nst(nstParameter2update, nstId)
    
    #Saving the NSI into the repositories and returning it
    NSI_string = vars(NSI)
    nsirepo_jsonresponse = nsi_repo.safe_nsi(NSI_string)
    return nsirepo_jsonresponse

def parseNewNSI(nst_json, nsi_json):
    LOG.info("NSI_MNGR: Parsing a new NSI from the user_info and the reference NST")
    uuid_nsi = str(uuid.uuid4())
    name = nsi_json['name']
    description = nsi_json['description']
    nstId = nsi_json['nstId']
    nstVendor = nst_json['vendor']
    nstName = nst_json['name']
    nstVersion = nst_json['version']
    flavorId = ""                                                                                            #TODO: where does it come from??
    sapInfo = ""                                                                                             #TODO: where does it come from??
    nsiState = "INSTANTIATED"
    instantiateTime = str(datetime.datetime.now().isoformat())
    terminateTime = ""
    scaleTime = ""
    updateTime = ""
    #netServInstance_Uuid = []    #these values are given later on, when the services are isntantiated and have a uuid given by the SP
    
    NSI=nsi.nsi_content(uuid_nsi, name, description, nstId, nstvendor, nstName, nstVersion, flavorId, sapInfo, 
                  nsiState, instantiateTime, terminateTime, scaleTime, updateTime)
    return NSI

def instantiateNetServices(NetServicesIDs):
    #instantiates required NetServices by sending requests to Sonata SP
    requestsID_list = []
    logging.debug('NetServicesIDs: '+str(NetServicesIDs))   
    for uuidNetServ_item in NetServicesIDs:
      instantiation_response = mapper.net_serv_instantiate(uuidNetServ_item)
      LOG.info("NSI_MNGR: INSTANTIATION_RESPONSE: " + str(instantiation_response))
      requestsID_list.append(instantiation_response['id'])
    logging.debug('requestsID_list: '+str(requestsID_list))
    return requestsID_list

def checkRequestsStatus(requestsUUID_list):
    counter=0
    for resquestUUID_item in requestsUUID_list:
      LOG.info("NSI_MNGR: Checking the instantiated service with uuid: " + str(resquestUUID_item))
      getRequest_response = mapper.getRequestedNetServInstance(resquestUUID_item)
      LOG.info("NSI_MNGR: Checking the instantiated service: " + str(getRequest_response))
      if(getRequest_response['status'] == 'READY'):
        counter=counter+1
    
    if (counter == len(requestsUUID_list)):
      return "READY"
    elif getRequest_response['status'] == 'ERROR':
      return "ERROR"
    else:
      return "INSTANTIATING"

##### TERMINATE NSI SECTION #####
def terminateNSI(nsiId, TerminOrder):
    LOG.info("NSI_MNGR: Terminate NSI with id: " +str(nsiId))
    jsonNSI = nsi_repo.get_saved_nsi(nsiId)
    
    #prepares the NSI object to manage with the info coming from repositories
    NSI=nsi.nsi_content(jsonNSI['uuid'], jsonNSI['name'], jsonNSI['description'], jsonNSI['nstId'], 
                    jsonNSI['vendor'], jsonNSI['nstInfoId'], jsonNSI['flavorId'], jsonNSI['sapInfo'], 
                    jsonNSI['nsiState'], jsonNSI['instantiateTime'], jsonNSI['terminateTime'], 
                    jsonNSI['scaleTime'], jsonNSI['updateTime'], jsonNSI['netServInstance_Uuid'])
    
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
          terminatedNetServ = mapper.net_serv_terminate(ServInstanceUuid_item)     #TODO: validate all related NetService instances are terminated
      
      repo_responseStatus = nsi_repo.delete_nsi(NSI.id)
      
      NSI.nsiState = "TERMINATED"
      return (vars(NSI))                                                          #TODO: check if it is the last NSI of the NST to change the "usageState" = "NOT_IN_USE"
    
    elif instan_time < termin_time:                                               #TODO: manage future termination orders
      NSI.terminateTime = str(termin_time)
      NSI.nsiState = "TERMINATED"
      
      update_NSI = vars(NSI)
      repo_responseStatus = nsi_repo.update_nsi(update_NSI, nsiId)
      
      return (vars(NSI))                                                          #TODO: check if it is the last NSI of the NST to change the "usageState" = "NOT_IN_USE"
    else:
      return ("Please specify a correct termination: 0 to terminate inmediately or a time value later than: " + NSI.instantiateTime+ ", to terminate in the future.")
    

##### GET NSI SECTION #####
def getNSI(nsiId):
    LOG.info("NSI_MNGR: Retrieving NSI with id: " +str(nsiId))
    nsirepo_jsonresponse = nsi_repo.get_saved_nsi(nsiId)

    return nsirepo_jsonresponse

def getAllNsi():
    LOG.info("NSI_MNGR: Retrieve all existing NSIs")
    nsirepo_jsonresponse = nsi_repo.getAll_saved_nsi()
    
    return nsirepo_jsonresponse