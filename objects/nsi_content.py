#!/usr/bin/python

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

class nsi_content:
    def __init__(self, id="", name="", description="", nstId="", vendor="", nstName="", nstVersion="", flavorId="", sapInfo="", nsiState="", instantiateTime="", terminateTime="", scaleTime="", updateTime="", sliceCallback="", netServInstance_Uuid=[]):
        self.id=id
        self.name=name
        self.description=description
        self.nstId=nstId                                          #in portal is the NST Reference
        self.vendor=vendor                                        # same vendor as the NetSlice Template
        self.nstName=nstName
        self.nstVersion=nstVersion
        self.flavorId=flavorId
        self.sapInfo=sapInfo                                      #this is used only when the instantiation has an error
        self.nsiState=nsiState                                    #values are Instantiated/Terminated TODO: check if there are there more
        self.instantiateTime=instantiateTime
        self.terminateTime=terminateTime
        self.scaleTime=scaleTime
        self.updateTime=updateTime
        self.sliceCallback=sliceCallback
        self.netServInstance_Uuid=netServInstance_Uuid
    
    def __str__(self):
        str_result =  "NSI: " + self.id \
                    + self.name \
                    + self.description \
                    + self.nstId \
                    + self.vendor \
                    + self.nstName \
                    + self.nstVersion \
                    + self.flavorId \
                    + self.sapInfo \
                    + self.nsiState \
                    + self.instantiateTime \
                    + self.terminateTime \
                    + self.scaleTime \
                    + self.updateTime \
                    + self.sliceCallback \
                    + self.netServInstance_Uuid
                    
        return str_result