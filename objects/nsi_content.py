#!/usr/bin/python

class nsi_content:
    def __init__(self, id="", name="", description="", nstId="", vendor="", nstInfoId="", flavorId="", sapInfo="", nsiState="", instantiateTime="", terminateTime="", scaleTime="", updateTime="", netServInstance_Uuid=[]):
        self.id=id
        self.name=name
        self.description=description
        self.nstId=nstId
        self.vendor=vendor
        self.nstInfoId=nstInfoId
        self.flavorId=flavorId
        self.sapInfo=sapInfo
        self.nsiState=nsiState
        self.instantiateTime=instantiateTime
        self.terminateTime=terminateTime
        self.scaleTime=scaleTime
        self.updateTime=updateTime
        self.netServInstance_Uuid=netServInstance_Uuid
    
    def __str__(self):
        str_result =  "NSI: " + self.id \
                    + self.name \
                    + self.description \
                    + self.nstId \
                    + self.vendor \
                    + self.nstInfoId \
                    + self.flavorId \
                    + self.sapInfo \
                    + self.nsiState \
                    + self.instantiateTime \
                    + self.terminateTime \
                    + self.scaleTime \
                    + self.updateTime \
                    + self.netServInstance_Uuid
                    
        return str_result