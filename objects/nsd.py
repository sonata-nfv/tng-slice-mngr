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

class nsd_content:
    def __init__(self, uuid="", name="", description="", vendor="", version="", md5="", author="", created="", status="", updated=""):
        self.uuid=uuid
        self.name=name
        self.description=description
        self.vendor=vendor
        self.version=version
        self.md5=md5
        self.author=author
        self.created=created
        self.status=status
        self.updated=updated
        
    def __str__(self):
        str_result = "NSD: " + self.uuid \
                    + self.name \
                    + self.description \
                    + self.vendor \
                    + self.version \
                    + self.md5 \
                    + self.author \
                    + self.created \
                    + self.status \
                    + self.updated    
        
        return str_result