"""
## Copyright (c) 2015 SONATA-NFV, 2017 5GTANGO [, ANY ADDITIONAL AFFILIATION]
## ALL RIGHTS RESERVED.
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
##
## Neither the name of the SONATA-NFV, 5GTANGO [, ANY ADDITIONAL AFFILIATION]
## nor the names of its contributors may be used to endorse or promote
## products derived from this software without specific prior written
## permission.
##
## This work has been performed in the framework of the SONATA project,
## funded by the European Commission under Grant number 671517 through
## the Horizon 2020 and 5G-PPP programmes. The authors would like to
## acknowledge the contributions of their colleagues of the SONATA
## partner consortium (www.sonata-nfv.eu).
##
## This work has been performed in the framework of the 5GTANGO project,
## funded by the European Commission under Grant number 761493 through
## the Horizon 2020 and 5G-PPP programmes. The authors would like to
## acknowledge the contributions of their colleagues of the 5GTANGO
## partner consortium (www.5gtango.eu).
"""

#CODE STRUCTURE INFORMATION
#This python script is divided in 4 sections: common functions, create NSI, terminate NSI and get NSI.

#!/usr/bin/python

import os, sys, logging, datetime, uuid, time, json
import dateutil.parser
from threading import Thread

import objects.nsi_content as nsi
import slice2ns_mapper.mapper as mapper
import slice_lifecycle_mgr.nsi_manager2repo as nsi_repo
import slice_lifecycle_mgr.nst_manager2catalogue as nst_catalogue

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("slicemngr:repo")
LOG.setLevel(logging.INFO)


#################### COMMON FUNCTIONS  ####################
#This function is used by the TWO MAIN ACTIONS (create/terminate)
def checkRequestsStatus(requestsUUID_list):
    counter_ready=0
    counter_error=0
    for resquestUUID_item in requestsUUID_list:
      getRequest_response = mapper.getRequestedNetServInstance(resquestUUID_item)
      LOG.info("NSI_MNGR: Information of the instantiated service: " + str(getRequest_response))
      if(getRequest_response['status'] == 'READY'):
        counter_ready=counter_ready+1
      if(getRequest_response['status'] == 'ERROR'):
        counter_error=counter_error+1
        
    if (counter_ready == len(requestsUUID_list)):
    
      return "READY"
      
    elif (counter_error > 0):
    
      return "ERROR"
      
    else:
    
      return "INSTANTIATING/TERMINATING"            


#################### CREATE NSI SECTION ####################
def createNSI(nsi_json):
    LOG.info("NSI_MNGR: Creating a new NSI")
    nstId = nsi_json['nstId']
    catalogue_response = nst_catalogue.get_saved_nst(nstId)
    nst_json = catalogue_response['nstd']
    
    LOG.info("NSI_MNGR: parsing the NSI object")
    NSI = parseNewNSI(nst_json, nsi_json)                                             #creates NSI with the received information
    
    LOG.info("NSI_MNGR: Sending request to instantiate services within the NST")
    serv_seq = 1                                                                      #to order the services within a slice in the protal
    for NetServ_item in nst_json['sliceServices']:
      data = {}
      data['name'] = nsi_name + "-" + NetServ_item['servname'] + "-" + str(serv_seq)
      data['service_uuid'] = NetServ_item['nsdID']
      data['callback'] = "http://tng-slice-mngr:5998/api/nsilcm/v1/nsi/on-change"     #passing endpoint to GK, later will send the updates about the slice instantiation
      #data['ingresses'] = []
      #data['egresses'] = []
      #data['blacklist'] = []
      data['sla_id'] = NetServ_item['slaID']
      
      instantiation_response = mapper.net_serv_instantiate(data)                      #requests to instantiate NSI services to the SP
      
      serviceInstance = {}
      serviceInstance['servId'] = instantiation_response['service']['uuid']
      serviceInstance['servName'] = instantiation_response['service']['name']
      serviceInstance['servInstanceId'] = instantiation_response['id']                #temporary assigns the request_ID until a service_instantiation_ID is given.
      serviceInstance['workingStatus'] = "INSTANTIATING"
      NSI.netServInstance_Uuid.append(serviceInstance)                                #adds the service instance into the NSI json
            
      serv_seq = serv_seq + 1
    
    LOG.info("NSI_MNGR: saving the slice instance information")
    NSI_string = vars(NSI)
    nsirepo_jsonresponse = nsi_repo.safe_nsi(NSI_string)                              #saving the NSI into the repositories
    
    return nsirepo_jsonresponse

def parseNewNSI(nst_json, nsi_json):
    LOG.info("NSI_MNGR: Parsing a new NSI from the user_info and the reference NST")
    uuid_nsi = str(uuid.uuid4())
    name = nsi_json['name']
    description = nsi_json['description']
    nstId = nsi_json['nstId']
    vendor = nst_json['vendor']
    nstName = nst_json['name']
    nstVersion = nst_json['version']
    flavorId = ""                                           #TODO: where does it come from??
    sapInfo = ""                                            #TODO: where does it come from??
    nsiState = "INSTANTIATING"
    instantiateTime = str(datetime.datetime.now().isoformat())
    terminateTime = ""
    scaleTime = ""
    updateTime = ""
    sliceReadyCallback = nsi_json['callback']                                          #URL used to call back the GK when the slice instance is READY/ERROR
    netServInstance_Uuid = []                                                          #values given when services are instantiated by the SP
    
    NSI=nsi.nsi_content(uuid_nsi, name, description, nstId, vendor, nstName, nstVersion, flavorId, 
                  sapInfo, nsiState, instantiateTime, terminateTime, scaleTime, updateTime, sliceReadyCallback, netServInstance_Uuid)
    return NSI
      
#################### UPDATES NSI SERVICES READY SECTION ####################
#updates a NSi being instantiated. If INSTANTIATED, calls the GK
def updateInstantiatingNSI(request_json):
    LOG.info("NSI_MNGR: get all NSIs.")
    nsi_list = nsi_repo.getAll_saved_nsi()
    
    LOG.info("NSI_MNGR: looking the id of the specific slice to modify.")
    if_found == False                                                                  #among all slices, looks for the ID of the slice to update
    for slice_item in nsi_list:
      servInstances_list = slice_item['netServInstance_Uuid']
      for servInstance_item in servInstances_list:
        if (servInstance_item['servInstanceId'] == request_json['id']):
          slice_id = slice_item['uuid']
          if_found = True
          break                                                                        #stops the second FOR loop if found
      if(if_found):
        break                                                                          #stops the first FOR loop if found
    
    LOG.info("NSI_MNGR: get the specific NSI to update the right service information.")
    jsonNSI = nsi_repo.get_saved_nsi(slice_id)
    
    LOG.info("NSI_MNGR: Modifies the specific service within the NSI.")
    for service_item in jsonNSI['netServInstance_Uuid']:                               #looks for the right service within the slice and updates it with the new data
      if (service_item['servInstanceId'] == request_json['id']):
        service_item['servInstanceId'] == request_json['instance_uuid']                #changes the id for the instance_uuid (the usage of id was temporal until this moment)
        service_item['workingStatus'] == request_json['status']
        jsonNSI['updateTime'] = str(datetime.datetime.now().isoformat())
        break
    
    LOG.info("NSI_MNGR: Checkin if the slice has all services ready/error or instantiating")
    allServicesReady == True                                                           #checks if all services are READY/ERROR to update the slice_status
    for service_item in jsonNSI['netServInstance_Uuid']:
      if (service_item['workingStatus'] == "NEW" or service_item['workingStatus'] == "INSTANTIATING"):
        allServicesReady == False
        break;
    
    if (allServicesReady == True):
      LOG.info("NSI_MNGR: All service instantiated, updating slice_status and reference in template")
      jsonNSI['nsiState'] = "INSTANTIATED"                                             #updates the slice status
      jsonNSI['updateTime'] = str(datetime.datetime.now().isoformat())
      updateNST_jsonresponse = addNSIinNST(nstId, nst_json, NSI.id)                    #updates NetSlice template list of slice_instances based on that template
     
    repo_responseStatus = nsi_repo.update_nsi(jsonNSI, slice_id)                       #sends the updated NetSlice instance to the repositories                              
    
    #INFO: leave it here (do not join with the previous IF, as...
    #... the multiple "return" depend on this order of the code lines.
    if (allServicesReady == True):
      LOG.info("NSI_MNGR: Notifying the GK that a slice is READY")
      thread_notify = Notify_Slice_Ready(jsonNSI['callback'], jsonNSI)                 #creates a thread with the callback URL to advise the GK this slice is READY
      thread_notify.start()
      
      return (repo_responseStatus, 201)
    
    return (repo_responseStatus, 200)


def addNSIinNST(nstId, nst_json, nsiId):                                               #updates the NST info: usageState and the list of NSI usign that NST
    if (nst_json['usageState'] == "NOT_IN_USE"):                                       #updates the usageState parameter
      nstParameter2update = "usageState=IN_USE"
      updatedNST_jsonresponse = nst_catalogue.update_nst(nstParameter2update, nstId)      

    nstParameter2update = "NSI_list_ref.append="+str(nsiId)                            #updates (adds) the list of NSIref of original NST
    updatedNST_jsonresponse = nst_catalogue.update_nst(nstParameter2update, nstId)
    logging.debug('NSI_MNGR: updated NSI reference list of the NST: '+str(updatedNST_jsonresponse))
    
    return updatedNST_jsonresponse

class Notify_Slice_Ready(Thread):
    def __init__(self, callback_endpoint, nsi_json):
      Thread.__init-_(self)
      self.callback_endpoint = callback_endpoint
      self.nsi_json = nsi_json
    def run(self):
      logging.debug('NSI_MNGR: Starts thread to call the GK slice is ready.')
      mapper.sliceInstantiated(self.callback_endpoint, self.nsi_json) 
      logging.debug('NSI_MNGR: Finishes thread to call the GK slice is ready.')
    
    
#################### TERMINATE NSI SECTION ####################
def terminateNSI(nsiId, TerminOrder):
    LOG.info("NSI_MNGR: Terminate NSI with id: " +str(nsiId))
    jsonNSI = nsi_repo.get_saved_nsi(nsiId)
    
    NSI=nsi.nsi_content(jsonNSI['uuid'], jsonNSI['name'], jsonNSI['description'], jsonNSI['nstId'], jsonNSI['vendor'], 
                    jsonNSI['nstName'], jsonNSI['nstVersion'], jsonNSI['flavorId'], jsonNSI['sapInfo'], jsonNSI['nsiState'], 
                    jsonNSI['instantiateTime'], jsonNSI['terminateTime'], jsonNSI['scaleTime'], jsonNSI['updateTime'], jsonNSI['netServInstance_Uuid'])
    LOG.info("NSI_MNGR_TERMINATE: The NSI to terminate: " +str(vars(NSI)))
    
    instan_time = dateutil.parser.parse(NSI.instantiateTime)                           #prepares the datetime values to work with them
    if (TerminOrder['terminateTime'] == "0"):
      termin_time = 0
    else:
      termin_time = dateutil.parser.parse(TerminOrder['terminateTime'])
    
    if termin_time == 0:                                                               #depending on the termin_time executes one action or another
      LOG.info("NSI_MNGR_TERMINATE: Selected to Terminate NOW!!!")
      NSI.terminateTime = str(datetime.datetime.now().isoformat())
      netServInstancesUUID_list = []
      for item in NSI.netServInstance_Uuid:                          #TODO: mirar si agafa com a json els strings o cal convertir-los a json...
        netServInstancesUUID_list.add(item["servInstanceId"])
        
      if (NSI.nsiState == "INSTANTIATED"):
        LOG.info("NSI_MNGR_TERMINATE: Sends terminate requests")
        requestsUUID_list = terminateNetServices(netServInstancesUUID_list)            #termination requests to all NetServiceInstances belonging to the NetSlice
      
        LOG.info("NSI_MNGR_TERMINATE: Terminate requests sent, cehcking if they are not READY anymore")
        allInstantiationsReady = "NEW"                                                 #checks if all instantiations in Sonata SP are TERMINATED to delete the NSI
        while (allInstantiationsReady == "NEW" or allInstantiationsReady == "INSTANTIATING/TERMINATING"):
          allInstantiationsReady = checkRequestsStatus(requestsUUID_list)
          time.sleep(30)
        
        LOG.info("NSI_MNGR_TERMINATE: Updates NSI info and sends it to repos")
        NSI.nsiState = "TERMINATED"
        update_NSI = vars(NSI)
        repo_responseStatus = nsi_repo.update_nsi(update_NSI, nsiId)
        
        LOG.info("NSI_MNGR_TERMINATE: Updates NST info and sends it to catalogues")
        removeNSIinNST(NSI.id, NSI.nstId)
      
      return (vars(NSI))
    
    elif (instan_time < termin_time):                                #TODO: manage future termination orders
      NSI.terminateTime = str(termin_time)
      NSI.nsiState = "TERMINATED"
      update_NSI = vars(NSI)
      repo_responseStatus = nsi_repo.update_nsi(update_NSI, nsiId)
      
      return (vars(NSI))
      
    else:
    
      return ("Please specify a correct termination: 0 to terminate inmediately or a time value later than: " + NSI.instantiateTime+ ", to terminate in the future.")
      
def terminateNetServices(NetServicesIDs):                                              #terminates NetServices by sending requests to Sonata SP
    requestsID_list = []
    logging.debug('NetServicesIDs: '+str(NetServicesIDs))
    LOG.info("NSI_MNGR_TERMINATE: NetServicesIDs to terminate: " +str(NetServicesIDs))
    for uuidNetServ_item in NetServicesIDs:
      termination_response = mapper.net_serv_terminate(uuidNetServ_item)
      LOG.info("NSI_MNGR: TERMINATION_response: " + str(termination_response))
      requestsID_list.append(termination_response['id'])
    logging.debug('requestsID_list: '+str(requestsID_list))
    LOG.info("NSI_MNGR_TERMINATE: requestsID_list to check status: " +str(requestsID_list))
    
    return requestsID_list

def removeNSIinNST(nsiId, nstId):
    LOG.info("NSI_MNGR_removeNSIinNST: updates NST info: instance_ref_list ")
    catalogue_response = nst_catalogue.get_saved_nst(nstId)                            #looks for the right NetSlice Template info
    nst_json = catalogue_response['nstd']

    nstParameter2update = "NSI_list_ref.pop="+str(nsiId)                               #deletes the terminated NetSlice instance uuid
    updatedNST_jsonresponse = nst_catalogue.update_nst(nstParameter2update, nstId)
    
    LOG.info("NSI_MNGR_removeNSIinNST: updates NST info: template_usagesState ")
    catalogue_response = nst_catalogue.get_saved_nst(nstId)                            #if there are no more NSI assigned to the NST, updates usageState parameter
    nst_json = catalogue_response['nstd']
    if not nst_json['NSI_list_ref']:
      if (nst_json['usageState'] == "IN_USE"):  
        nstParameter2update = "usageState=NOT_IN_USE"
        updatedNST_jsonresponse = nst_catalogue.update_nst(nstParameter2update, nstId)  
    


#################### GET NSI SECTION ####################
def getNSI(nsiId):
    LOG.info("NSI_MNGR: Retrieving NSI with id: " +str(nsiId))
    nsirepo_jsonresponse = nsi_repo.get_saved_nsi(nsiId)

    return nsirepo_jsonresponse

def getAllNsi():
    LOG.info("NSI_MNGR: Retrieve all existing NSIs")
    nsirepo_jsonresponse = nsi_repo.getAll_saved_nsi()
    
    return nsirepo_jsonresponse