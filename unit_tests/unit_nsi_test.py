#!/usr/local/bin/python3.4

import os
import json
import unittest
import xmlrunner
import uuid
import subprocess
import time
from unittest.mock import patch
from datetime import datetime
from configparser import ConfigParser

import objects.nsi_content as nsi
import slice_lifecycle_mgr.nsi_manager2repo as nsi_repo
from database import database as db

from slice_lifecycle_mgr.nsi_manager import parseNewNSI


class TestCase(unittest.TestCase):
    #def setUp(self):

    #def tearDown():

    def test_create_NSI(self):
        #Prepares MOCK NST/NSI objects to send to the tested function      
        #mock_nst_json ={"author": "5gTango","name": "5gtango_NST_name","notificationTypes": "","nstNsdIds": ["6a01afdc-9d42-4bc9-866c-a8a3868fdf5e"],"onboardingState": "ENABLED","operationalState": "ENABLED","usageState": "NOT_IN_USE","userDefinedData": "","vendor": "5gTango","version": "1.0"}
        mock_nst_json = {"name":"NST_Example","description":"This is the description of a NST.","version":"3.0","author":"CTTC","vendor":"5GTango","SNSSAI_identifier":{"slice-service-type":"eMBB"},"onboardingState":"ENABLED","operationalState":"ENABLED","usageState":"NOT_IN_USE","5qi_value":3,"slice_ns_subnets":[{"id":"Service_subnet_1","nsd-ref":"6a01afdc-9d42-4bc9-866c-a8a3868fdf5e","nsd-name":"Service_1","sla-name":"GOLD_SLA_2","sla-ref":"aabbccdd-9d42-4bc9-866c-a8a3868fdf5e","is-shared":False},{"id":"Service_subnet_2","nsd-ref":"eeff1122-9d42-4bc9-866c-a8a3868fdf5e","nsd-name":"Service_2","sla-name":"GOLD_SLA_2","sla-ref":"44556677-9d42-4bc9-866c-a8a3868fdf5e","is-shared":True},{"id":"Service_subnet_3","nsd-ref":"99887766-9d42-4bc9-866c-a8a3868fdf5e","nsd-name":"Service_3","sla-name":"None","sla-ref":"None","is-shared":False}],"slice_vld":[{"id":"mgmt","name":"mgmt","mgmt-network":True,"type":"E-LAN","nsd-connection-point-ref":[{"subnet-ref":"Service_subnet_1","nsd-cp-ref":"cp_mgmt"},{"subnet-ref":"Service_subnet_2","nsd-cp-ref":"cp_mgmt"},{"subnet-ref":"Service_subnet_3","nsd-cp-ref":"cp_mgmt"}]},{"id":"data-east","name":"data-east","type":"E-LAN","nsd-connection-point-ref":[{"subnet-ref":"Service_subnet_1","nsd-cp-ref":"cp_1"},{"subnet-ref":"Service_subnet_2","nsd-cp-ref":"cp_1"}]},{"id":"data_west","name":"data_west","type":"E-LAN","nsd-connection-point-ref":[{"subnet-ref":"Service_subnet_2","nsd-cp-ref":"cp_2"},{"subnet-ref":"Service_subnet_3","nsd-cp-ref":"cp_1"}]}]}
        mock_nsi_json = {"name": "tango_NSI", "description": "5gTango_descriptor", "nstId": "096c26f9-6142-43d2-8521-57cea9e76c6c", 'callback':'gtk_callback', 'datacenter':'00000000-0000-0000-0000-000000000000'}
        
        #Creates NSI object and json (to send to the repositories in integration tests)
        response_NSI = parseNewNSI(mock_nst_json, mock_nsi_json)
        
        self.assertEqual(response_NSI["name"], "tango_NSI")
        self.assertEqual(response_NSI["vendor"], "5GTango")
        self.assertEqual(response_NSI["description"], "5gTango_descriptor")
        self.assertEqual(response_NSI["nsi-status"], "INSTANTIATING")
        self.assertEqual(response_NSI["nst-ref"], "096c26f9-6142-43d2-8521-57cea9e76c6c")
        
    
#    def test_get_NSI(self):
#        #Test create NST before NSI
#        NetService_uuid = str(uuid.uuid4())
#        response = self.app.post("/api/nst/v1/descriptors", data=json.dumps(dict(name="5gtango_NST_name_2", version="1.0", author="5gtango", vendor="5gtango_vendor",
#                                  nstNsdIds=[dict(NsdId=NetService_uuid)])),content_type='application/json')
#        
#        self.assertEqual(response.status_code, 201)
#        resp_json = json.loads(response.data)
#        
#        NST_uuid = resp_json["uuid"]
#        
#        #Test create NSI
#        response = self.app.post("/api/nsilcm/v1/nsi", data=json.dumps(dict(name="5gtango_NSI_name", decription="NSI_description", nstId=NST_uuid)),content_type='application/json')
#        self.assertEqual(response.status_code, 200)
#        resp_json = json.loads(response.data)
#        
#        NSI_uuid = resp_json["id"]
#        
#        #Test get all NSIs
#        response = self.app.get("/api/nsilcm/v1/nsi")
#        self.assertEqual(response.status_code, 200)
#        resp_json = json.loads(response.data)
#
#        NSI_list = []
#        for i in resp_json:
#            NSI_list.append(i["id"])
#
#        self.assertTrue(NST_uuid in NST_list)
#        
#        #Test get a specific NSI
#        response = self.app.get("/api/nsilcm/v1/nsi/%s" %NSI_uuid)
#        self.assertEqual(response.status_code, 200)
#        
#        resp_json = json.loads(response.data)
#        self.assertEqual(resp_json["id"], NSI_uuid)
#
#    def test_terminate_NSI(self):
#        #Test create NST before NSI
#        NetService_uuid = str(uuid.uuid4())
#        response = self.app.post("/api/nst/v1/descriptors", data=json.dumps(dict(name="5gtango_NST_name", version="1.0", author="5gtango", vendor="5gtango_vendor",
#                                  nstNsdIds=[dict(NsdId=NetService_uuid)])),content_type='application/json')
#        
#        self.assertEqual(response.status_code, 201)
#        resp_json = json.loads(response.data)
#        
#        NST_uuid = resp_json["uuid"]
#        
#        #Test create NSI
#        response = self.app.post("/api/nsilcm/v1/nsi", data=json.dumps(dict(name="5gtango_NSI_name", decription="NSI_description", nstId=NST_uuid)),content_type='application/json')
#        self.assertEqual(response.status_code, 200)
#        resp_json = json.loads(response.data)
#        NSI_id = resp_json["id"]
#        
#        #Test terminate in future
#        response = self.app.post("/api/nsilcm/v1/nsi/"+str(NSI_id)+"/terminate", data=json.dumps(dict(terminateTime = "2019-04-11T10:55:30.560")),content_type='application/json')
#        self.assertEqual(response.status_code, 200)
#        resp_json = json.loads(response.data)
#        NSI_terminateTime = resp_json["terminateTime"]
#        self.assertEqual(NSI_terminateTime, "2019-04-11T10:55:30.560")
#        
#        #Test terminate instantly
#        response = self.app.post("/api/nsilcm/v1/nsi/"+str(NSI_id)+"/terminate", data=json.dumps(dict(terminateTime = "0")),content_type='application/json')
#        self.assertEqual(response.status_code, 200)
        
        

if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))