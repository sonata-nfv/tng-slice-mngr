#!/usr/local/bin/python3.4
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

import os, sys, logging, uuid, json, time
import objects.nst_content as nst

import slice_lifecycle_mgr.nst_manager2catalogue as nst_catalogue
import slice2ns_mapper.mapper as mapper
import database.database as db

#TODO: apply it
# definition of LOG variable to make the slice logs idetified among the other possible 5GTango components.
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("slicemngr:repo")
LOG.setLevel(logging.INFO)

######################### NETWORK SLICE TEMPLATE CREATION/UPDATE/REMOVE SECTION ##############################
# Creates a NST and sends it to catalogues
def create_nst(jsondata):
  logging.info("NST_MNGR: Ceating a new NST with the following services: " +str(jsondata))

  #TODO: validate that no existing NSTD has the same NAME-VENDOR-VERSION
  nstcatalogue_jsonresponse = nst_catalogue.get_all_saved_nst()
  if nstcatalogue_jsonresponse:
    for nstd_item in nstcatalogue_jsonresponse:
      if (nstd_item['nstd']['name'] == jsondata['name'] and nstd_item['nstd']['vendor'] == jsondata['vendor'] and nstd_item['nstd']['version'] == jsondata['version']):
        nstd_duplicated = True
        return '{"error_msg": "NSTD with this description parameters (NAME, VENDOR or VERSION) already exists."}', 400
  
  # Get the current services list to get the uuid for each slice-subnet (NSD) reference
  current_services_list = mapper.getListNetServices()

  # Looks for the NSD that fullfils the service conditions (name/vendor/version) ofthe subnet within the slice.
  for subnet_item  in jsondata["slice_ns_subnets"]:
    for service_item in current_services_list:
      logging.info("NST_MNGR: subnet_item[nsd-name]: " + str(subnet_item["nsd-name"]) + "service_item[name]: " + str(service_item["name"]))
      logging.info("NST_MNGR: subnet_item[nsd-vendor]: " + str(subnet_item["nsd-vendor"]) + "service_item[vendor]: " + str(service_item["vendor"]))
      logging.info("NST_MNGR: subnet_item[nsd-version]: " + str(subnet_item["nsd-version"]) + "service_item[version]: " + str(service_item["version"]))
      if (subnet_item["nsd-name"] == service_item["name"] and subnet_item["nsd-vendor"] == service_item["vendor"] and subnet_item["nsd-version"] == service_item["version"]):
        subnet_item["nsd-ref"] = service_item["uuid"]
      else:
        return '{"error_msg": "This NSTD tries has a non-existing NSD, check your NSDs parameters (NAME, VENDOR or VERSION)."}', 400
  
  #Sends the new NST to the catalogues (DB)
  if nstd_duplicated == False and nsd_ok == True:
    nstcatalogue_jsonresponse = nst_catalogue.safe_nst(jsondata)
    return nstcatalogue_jsonresponse[0], nstcatalogue_jsonresponse[1]

# Updates the information of a selected NST in catalogues
def updateNST(nstId, NST_string):
  logging.info("NST_MNGR: Updating NST with id: " +str(nstId))
  nstcatalogue_jsonresponse = nst_catalogue.update_nst(update_NST, nstId)
  
  return nstcatalogue_jsonresponse

# Deletes a NST kept in catalogues
def remove_nst(nstId):
  logging.info("NST_MNGR: Delete NST with id: " + str(nstId))
  nstcatalogue_jsonresponse = nst_catalogue.get_saved_nst(nstId)
  if (nstcatalogue_jsonresponse['nstd']["usageState"] == "NOT_IN_USE"):
    nstcatalogue_jsonresponse = nst_catalogue.delete_nst(nstId)
    return nstcatalogue_jsonresponse
  else:
    return 403


############################################ GET NST SECTION ############################################
# Returns the information of all the NST in catalogues
def get_all_nst():
  logging.info("NST_MNGR: Retrieving all existing NSTs")
  nstcatalogue_jsonresponse = nst_catalogue.get_all_saved_nst()
  
  if (nstcatalogue_jsonresponse):
    return (nstcatalogue_jsonresponse, 200)
  else:
    return ('{"error":"There are no NSTD in the db."}', 500)

# Returns the information of a selected NST in catalogues
def get_nst(nstId):
  logging.info("NST_MNGR: Retrieving NST with id: " + str(nstId))
  nstcatalogue_jsonresponse = nst_catalogue.get_saved_nst(nstId)

  if (nstcatalogue_jsonresponse):
    return (nstcatalogue_jsonresponse, 200)
  else:
    return ('{"error":"There is no NSTD with this uuid in the db."}', 500)
