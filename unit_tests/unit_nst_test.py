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

import slice_lifecycle_mgr.nst_manager2catalogue
from slice_lifecycle_mgr.nst_manager import createNST
from database import database as db


class TestCase(unittest.TestCase):
    def setUp(self):
        config = ConfigParser()
        config.read('config.cfg')
        db.settings = config
            
#    def tearDown(self):
#        nst_dict.del
    
    @patch('slice_lifecycle_mgr.nst_manager2catalogue.requests.post')
    def test_create_NST(self, mock_createNST):
        #Mock answer for the request to the catalogues     
        mock_createNST.return_value.status_code = 201
        mock_createNST.return_value.text = '{"created_at": "2018-06-08T10:36:53.425+00:00","md5": "5024cfde7637ab98f086ff51bd158bc9","nstd": {"name":"NST_Example","description":"This is the description of a NST.","version":"3.0","author":"CTTC","vendor":"5GTango","SNSSAI_identifier":{"slice-service-type":"eMBB"},"onboardingState":"ENABLED","operationalState":"ENABLED","usageState":"NOT_IN_USE","5qi_value":3,"slice_ns_subnets":[{"id":"Service_subnet_1","nsd-ref":"6a01afdc-9d42-4bc9-866c-a8a3868fdf5e","nsd-name":"Service_1","sla-name":"GOLD_SLA_2","sla-ref":"aabbccdd-9d42-4bc9-866c-a8a3868fdf5e","is-shared":false},{"id":"Service_subnet_2","nsd-ref":"eeff1122-9d42-4bc9-866c-a8a3868fdf5e","nsd-name":"Service_2","sla-name":"GOLD_SLA_2","sla-ref":"44556677-9d42-4bc9-866c-a8a3868fdf5e","is-shared":true},{"id":"Service_subnet_3","nsd-ref":"99887766-9d42-4bc9-866c-a8a3868fdf5e","nsd-name":"Service_3","sla-name":"None","sla-ref":"None","is-shared":false}],"slice_vld":[{"id":"mgmt","name":"mgmt","mgmt-network":true,"type":"E-LAN","nsd-connection-point-ref":[{"subnet-ref":"Service_subnet_1","nsd-cp-ref":"cp_mgmt"},{"subnet-ref":"Service_subnet_2","nsd-cp-ref":"cp_mgmt"},{"subnet-ref":"Service_subnet_3","nsd-cp-ref":"cp_mgmt"}]},{"id":"data-east","name":"data-east","type":"E-LAN","nsd-connection-point-ref":[{"subnet-ref":"Service_subnet_1","nsd-cp-ref":"cp_1"},{"subnet-ref":"Service_subnet_2","nsd-cp-ref":"cp_1"}]},{"id":"data_west","name":"data_west","type":"E-LAN","nsd-connection-point-ref":[{"subnet-ref":"Service_subnet_2","nsd-cp-ref":"cp_2"},{"subnet-ref":"Service_subnet_3","nsd-cp-ref":"cp_1"}]}]},"signature": null,"status": "active","updated_at": "2018-06-08T10:36:53.425+00:00","username": null,"uuid": "096c26f9-6142-43d2-8521-57cea9e76c6c"}'
        
        #Prepares received information from portal
        #NetService_1_uuid = str(uuid.uuid4())
        #NetService_2_uuid = str(uuid.uuid4())
        mock_jsondata = {"name":"NST_Example","description":"This is the description of a NST.","version":"3.0","author":"CTTC","vendor":"5GTango","SNSSAI_identifier":{"slice-service-type":"eMBB"},"onboardingState":"ENABLED","operationalState":"ENABLED","usageState":"NOT_IN_USE","5qi_value":3,"slice_ns_subnets":[{"id":"Service_subnet_1","nsd-ref":"6a01afdc-9d42-4bc9-866c-a8a3868fdf5e","nsd-name":"Service_1","sla-name":"GOLD_SLA_2","sla-ref":"aabbccdd-9d42-4bc9-866c-a8a3868fdf5e","is-shared":false},{"id":"Service_subnet_2","nsd-ref":"eeff1122-9d42-4bc9-866c-a8a3868fdf5e","nsd-name":"Service_2","sla-name":"GOLD_SLA_2","sla-ref":"44556677-9d42-4bc9-866c-a8a3868fdf5e","is-shared":true},{"id":"Service_subnet_3","nsd-ref":"99887766-9d42-4bc9-866c-a8a3868fdf5e","nsd-name":"Service_3","sla-name":"None","sla-ref":"None","is-shared":false}],"slice_vld":[{"id":"mgmt","name":"mgmt","mgmt-network":true,"type":"E-LAN","nsd-connection-point-ref":[{"subnet-ref":"Service_subnet_1","nsd-cp-ref":"cp_mgmt"},{"subnet-ref":"Service_subnet_2","nsd-cp-ref":"cp_mgmt"},{"subnet-ref":"Service_subnet_3","nsd-cp-ref":"cp_mgmt"}]},{"id":"data-east","name":"data-east","type":"E-LAN","nsd-connection-point-ref":[{"subnet-ref":"Service_subnet_1","nsd-cp-ref":"cp_1"},{"subnet-ref":"Service_subnet_2","nsd-cp-ref":"cp_1"}]},{"id":"data_west","name":"data_west","type":"E-LAN","nsd-connection-point-ref":[{"subnet-ref":"Service_subnet_2","nsd-cp-ref":"cp_2"},{"subnet-ref":"Service_subnet_3","nsd-cp-ref":"cp_1"}]}]}
        
        #Testing the function to create NST
        response = createNST(mock_jsondata)

        #Comparing response values
        NST_uuid = response["uuid"]
        NST_name = response["nstd"]["name"]
        NST_author = response["nstd"]["author"]
        NST_vendor = response["nstd"]["vendor"]
        NST_onboardingState = response["nstd"]["onboardingState"]
        NST_operationalState = response["nstd"]["operationalState"]
        
        self.assertEqual(NST_uuid, "096c26f9-6142-43d2-8521-57cea9e76c6c")
        self.assertEqual(NST_name, "NST_Example")
        self.assertEqual(NST_author, "CTTC")
        self.assertEqual(NST_vendor, "5GTango")
        self.assertEqual(NST_onboardingState, "ENABLED")
        self.assertEqual(NST_operationalState, "ENABLED")
    
#    def test_get_NST(self):
#        NetService_1_uuid = str(uuid.uuid4())
#
#        #Creates two NSTs
#        response = self.app.post("/api/nst/v1/descriptors"), data=json.dumps(dict(name="sonata_NST_name", version="1.0", author="sonata", vendor="sonata_vendor",
#                                  nstNsdIds=[dict(NsdId=NetService_1_uuid)])),content_type='application/json')
#        
#        self.assertEqual(response.status_code, 201)
#        
#        response = self.app.post("/api/nst/v1/descriptors"), data=json.dumps(dict(name="5gtango_NST_name", version="1.0", author="5gtango", vendor="5gtango_vendor",
#                                  nstNsdIds=[dict(NsdId=NetService_1_uuid)])),content_type='application/json')
#        
#        self.assertEqual(response.status_code, 201)
#        resp_json = json.loads(response.data)
#        NST_uuid = str(resp_json["uuid"])
#        
#        #Test get all NSTs
#        response = self.app.get("/api/nst/v1/descriptors")
#        self.assertEqual(response.status_code, 200)
#        resp_json = json.loads(response.data)
#
#        NST_list = []
#        for i in resp_json:
#            NST_list.append(i["uuid"])
#
#        self.assertTrue(NST_uuid in NST_list)
#        
#        #Test get a specific NST
#        response = self.app.get("/api/nst/v1/descriptors/%s" %NST_uuid)
#        self.assertEqual(response.status_code, 200)
#        resp_json = json.loads(response.data)
#
#        self.assertEqual(NST_uuid, resp_json["uuid"])
#
#    def test_delete_NST(self):
#        NetService_1_uuid = str(uuid.uuid4())
#
#        # Adding active License
#        response = self.app.post("/api/nst/v1/descriptors"), data=json.dumps(dict(name="5gtango_NST_name", version="1.0", author="5gtago", vendor="5gtango_vendor",
#                                  nstNsdIds=[dict(NsdId=NetService_1_uuid)])),content_type='application/json')
#        
#        self.assertEqual(response.status_code, 201)
#        resp_json = json.loads(response.data)
#        NST_uuid = str(resp_json["uuid"])
#               
#        # Test get a specific license if is valid
#        response = self.app.delete("/api/nst/v1/descriptors/%s" %NST_uuid)
#        self.assertEqual(response.status_code, 204)
        

if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))