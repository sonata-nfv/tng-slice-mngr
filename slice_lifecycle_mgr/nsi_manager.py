#!/usr/bin/python

import os, sys, logging, datetime, uuid, time
import dateutil.parser

import objects.nsi_content as nsi
import slice2ns_mapper.mapper as mapper
import database.database as db

##OTHER functions (used by NSI functions)
def check_requests_status(token, requestsID_list):
    counter=0
    for resquestID_item in requestsID_list:
      getRequest_response = mapper.getRequestedNetServInstance(token, resquestID_item)
      
      print ("--------------------------------------------------------")
      print (getRequest_response)
      print (len(requestsID_list))
      print ("--------------------------------------------------------")
      
      if(getRequest_response['status'] == 'READY'):
        counter=coutner+1
    
    if (counter == len(requestsID_list)):
      return True
    else:
      return False


##NSI functions
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
  
    #sends requests to SonataSP to instantiate the required NetServices
    NST = db.nst_dict.get(NSI.nstId)
    requestsID_list = []
    for uuidNetServ_item in NST.nstNsdIds:
      instantiation_response = mapper.net_serv_instantiate(token, uuidNetServ_item)
      print ("##################")
      print(instantiation_response['id'])
      print ("##################")
      requestsID_list.append(instantiation_response['id'])
    
    #checks if the requestes instantiations are READY so, the informatiotion can be stored  
    allInstantiationsReady = False
    while (allInstantiationsReady == False):
      allInstantiationsReady = check_requests_status(token, requestsID_list)
      time.sleep(20)
    
    for request_uuid_item in requestsID_list:
      instantiation_response = mapper.getNetServInstance(token, request_uuid_item)
      NSI.netServInstance_Uuid.append(instantiation_response['service_instance_uuid'])

    #updates nstUsageState parameter
    if NST.nstUsageState == "NOT_IN_USE":
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