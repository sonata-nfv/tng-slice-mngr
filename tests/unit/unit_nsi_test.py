#!/usr/bin/python

import os
import json
import unittest
import xmlrunner
import uuid
import subprocess
import time
from datetime import datetime
from app import app, db

class TestCase(unittest.TestCase):
    def setUp():
    
    def tearDown():
    
    def test_create_NSI(self):
        #Test create NST before NSI
        NetService_uuid = str(uuid.uuid4())
        
        response = self.app.post("/api/nst/v1/descriptors", data=json.dumps(dict(name="5gtango_NST_name", version="1.0", author="5gtango", vendor="5gtango_vendor",
                                  nstNsdIds=[dict(NsdId=NetService_uuid)])),content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        resp_json = json.loads(response.data)
        
        NST_uuid = resp_json["uuid"]
        
        #Test create NSI
        response = self.app.post("/api/nsilcm/v1/nsi", data=json.dumps(dict(name="5gtango_NSI_name", decription="NSI_description", nstId=NST_uuid)),content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        resp_json = json.loads(response.data)
        
        NSI_uuid = resp_json["id"]
        NSI_name = respo_json["name"]
        NSI_nsiState = resp_json["nsiState"]
        NSI_nstId = resp_json["nstId"]
        
        self.assertEqual(NSI_name, "5gtango_NSI_name")
        self.assertEqual(NSI_usageState, "INSTANTIATED")
        self.assertEqual(NSI_nstId, NST_uuid)
        
        #Test validate the NST usageState is udpated to "IN_USE" status
        response = self.app.get("/api/nst/v1/descriptors/%s" %NST_uuid)
        self.assertEqual(response.status_code, 200)
        resp_json = json.loads(response.data)
        
        NST_usageState = resp_json["nstd"]["usageState"]
        self.assertEqual(NST_usageState, "IN_USE")
        
    
    def test_get_NSI(self):
        #Test create NST before NSI
        NetService_uuid = str(uuid.uuid4())
        response = self.app.post("/api/nst/v1/descriptors", data=json.dumps(dict(name="5gtango_NST_name", version="1.0", author="5gtango", vendor="5gtango_vendor",
                                  nstNsdIds=[dict(NsdId=NetService_uuid)])),content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        resp_json = json.loads(response.data)
        
        NST_uuid = resp_json["uuid"]
        
        #Test create NSI
        response = self.app.post("/api/nsilcm/v1/nsi", data=json.dumps(dict(name="5gtango_NSI_name", decription="NSI_description", nstId=NST_uuid)),content_type='application/json')
        self.assertEqual(response.status_code, 200)
        resp_json = json.loads(response.data)
        
        NSI_uuid = resp_json["id"]
        
        #Test get all NSIs
        response = self.app.get("/api/nsilcm/v1/nsi")
        self.assertEqual(response.status_code, 200)
        resp_json = json.loads(response.data)

        NSI_list = []
        for i in resp_json:
            NSI_list.append(i["id"])

        self.assertTrue(NST_uuid in NST_list)
        
        #Test get a specific NSI
        response = self.app.get("/api/nsilcm/v1/nsi/%s" %NSI_uuid)
        self.assertEqual(response.status_code, 200)
        
        resp_json = json.loads(response.data)
        self.assertEqual(resp_json["id"], NSI_uuid)

    def test_terminate_NSI(self):
        #Test create NST before NSI
        NetService_uuid = str(uuid.uuid4())
        response = self.app.post("/api/nst/v1/descriptors", data=json.dumps(dict(name="5gtango_NST_name", version="1.0", author="5gtango", vendor="5gtango_vendor",
                                  nstNsdIds=[dict(NsdId=NetService_uuid)])),content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        resp_json = json.loads(response.data)
        
        NST_uuid = resp_json["uuid"]
        
        #Test create NSI
        response = self.app.post("/api/nsilcm/v1/nsi", data=json.dumps(dict(name="5gtango_NSI_name", decription="NSI_description", nstId=NST_uuid)),content_type='application/json')
        self.assertEqual(response.status_code, 200)
        resp_json = json.loads(response.data)
        NSI_id = resp_json["id"]
        
        #Test terminate in future
        response = self.app.post("/api/nsilcm/v1/nsi/"+str(NSI_id)+"/terminate", data=json.dumps(dict(terminateTime = "2019-04-11T10:55:30.560")),content_type='application/json')
        self.assertEqual(response.status_code, 200)
        resp_json = json.loads(response.data)
        NSI_terminateTime = resp_json["terminateTime"]
        self.assertEqual(NSI_terminateTime, "2019-04-11T10:55:30.560")
        
        #Test terminate instantly
        response = self.app.post("/api/nsilcm/v1/nsi/"+str(NSI_id)+"/terminate", data=json.dumps(dict(terminateTime = "0")),content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        

if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))