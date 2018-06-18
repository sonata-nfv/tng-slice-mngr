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

import slice_lifecycle_mgr.nst_manager2catalogue as nst_catalogue
#from main

class TestCase(unittest.TestCase):
#    def setUp():
#        nst_dict={}
#        self.app = main.app.test_client()
#    
#    def tearDown():
#        nst_dict.del
    
    @patch('nst_catalogue.requestst.post')
    def test_create_NST(self, mock_createNST):
        NetService_1_uuid = str(uuid.uuid4())
        NetService_2_uuid = str(uuid.uuid4())
        data=json.dumps(dict(name="5gtango_NST_name",version="1.0", author="5gtango",vendor="5gtango_vendor",
                        nstNsdIds=[dict(NsdId=NetService_1_uuid),dict(NsdId=NetService_2_uuid)]))
        
        mock_createNST.return_value.status_code = 201
        response = createNST(data)
        
        self.assertEqual(response.status_code, 201)
        #resp_json = json.loads(response.data)
        
#        NST_uuid = resp_json["uuid"]
#        NST_name = resp_json["nstd"]["name"]
#        NST_usageState = resp_json["nstd"]["usageState"]
#        NST_onboardingState = resp_json["nstd"]["onboardingState"]
#        NST_operationalState = resp_json["nstd"]["operationalState"]
#        
#        self.assertEqual(NST_name, "5gtango_NST_name")
#        self.assertEqual(NST_usageState, "NOT_IN_USE")
#        self.assertEqual(NST_onboardingState, "ENABLED")
#        self.assertEqual(NST_operationalState, "ENABLED")
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