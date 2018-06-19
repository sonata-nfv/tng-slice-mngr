#!/usr/bin/python

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
#from main

class TestCase(unittest.TestCase):
    def setUp(self):
        config = ConfigParser()
        config.read('config.cfg')
        db.settings = config
#        nst_dict={}
#        self.app = main.app.test_client()
            
#    def tearDown(self):
#        nst_dict.del
    
    @patch('slice_lifecycle_mgr.nst_manager2catalogue.requests.post')
    def test_create_NST(self, mock_createNST):
        #Mock answer for the request to the catalogues     
        mock_createNST.return_value.status_code = 201
        mock_createNST.return_value.text = '{"created_at": "2018-06-08T10:36:53.425+00:00","md5": "5024cfde7637ab98f086ff51bd158bc9","nstd": {"author": "5gTango","name": "5gtango_NST_name","notificationTypes": "","nstNsdIds": ["6a01afdc-9d42-4bc9-866c-a8a3868fdf5e"],"onboardingState": "ENABLED","operationalState": "ENABLED","usageState": "NOT_IN_USE","userDefinedData": "","vendor": "5gTango","version": "1.0"},"signature": null,"status": "active","updated_at": "2018-06-08T10:36:53.425+00:00","username": null,"uuid": "096c26f9-6142-43d2-8521-57cea9e76c6c"}'
        
        #Preapres de information received from the protal.
        NetService_1_uuid = str(uuid.uuid4())
        NetService_2_uuid = str(uuid.uuid4())
        data = {"name":"5gtango_NST_name", "version":"1.0", "author":"5gtango", "vendor":"5gTango", "nstNsdIds":[{"NsdId":"52047455-5792-4ce7-8809-2f56c4a876bd"},{"NsdId":"fb050678-2b12-432a-8ee2-a2dff777510f"}]}
        
        #Testing the function to create NST
        response = createNST(data)
        
        #self.assertEqual(response.status_code, 201)
        
        NST_uuid = response["uuid"]
        NST_name = response["nstd"]["name"]
        NST_author = response["nstd"]["author"]
        NST_usageState = response["nstd"]["usageState"]
        NST_onboardingState = response["nstd"]["onboardingState"]
        NST_operationalState = response["nstd"]["operationalState"]
        
        self.assertEqual(NST_uuid, "096c26f9-6142-43d2-8521-57cea9e76c6c")
        self.assertEqual(NST_name, "5gtango_NST_name")
        self.assertEqual(NST_author, "5gTango")
        self.assertEqual(NST_usageState, "NOT_IN_USE")
        self.assertEqual(NST_onboardingState, "ENABLED")
        self.assertEqual(NST_operationalState, "ENABLED")
#    
##    def test_get_NST(self):
##        NetService_1_uuid = str(uuid.uuid4())
##
##        #Creates two NSTs
##        response = self.app.post("/api/nst/v1/descriptors"), data=json.dumps(dict(name="sonata_NST_name", version="1.0", author="sonata", vendor="sonata_vendor",
##                                  nstNsdIds=[dict(NsdId=NetService_1_uuid)])),content_type='application/json')
##        
##        self.assertEqual(response.status_code, 201)
##        
##        response = self.app.post("/api/nst/v1/descriptors"), data=json.dumps(dict(name="5gtango_NST_name", version="1.0", author="5gtango", vendor="5gtango_vendor",
##                                  nstNsdIds=[dict(NsdId=NetService_1_uuid)])),content_type='application/json')
##        
##        self.assertEqual(response.status_code, 201)
##        resp_json = json.loads(response.data)
##        NST_uuid = str(resp_json["uuid"])
##        
##        #Test get all NSTs
##        response = self.app.get("/api/nst/v1/descriptors")
##        self.assertEqual(response.status_code, 200)
##        resp_json = json.loads(response.data)
##
##        NST_list = []
##        for i in resp_json:
##            NST_list.append(i["uuid"])
##
##        self.assertTrue(NST_uuid in NST_list)
##        
##        #Test get a specific NST
##        response = self.app.get("/api/nst/v1/descriptors/%s" %NST_uuid)
##        self.assertEqual(response.status_code, 200)
##        resp_json = json.loads(response.data)
##
##        self.assertEqual(NST_uuid, resp_json["uuid"])
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