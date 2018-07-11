#!/usr/bin/python

class nsi_content:
    def __init__(self, id="", name="", description="", nstId="", nstVendor="", nstName="", nstVersion="", flavorId="", sapInfo="", nsiState="", instantiateTime="", terminateTime="", scaleTime="", updateTime="", netServInstance_Uuid=[]):
        self.id=id
        self.name=name
        self.description=description
        self.nstId=nstId                                          #in portal is the NST Reference
        self.nstVendor=vendor
        self.nstName=nstName
        self.nstVersion=nstVersion
        self.flavorId=flavorId
        self.sapInfo=sapInfo
        self.nsiState=nsiState                                    #values are Instantiated/Terminated TODO: check if there are there more
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
                    + self.nstVendor \
                    + self.nstName \
                    + self.nstVersion \
                    + self.flavorId \
                    + self.sapInfo \
                    + self.nsiState \
                    + self.instantiateTime \
                    + self.terminateTime \
                    + self.scaleTime \
                    + self.updateTime \
                    + self.netServInstance_Uuid
                    
        return str_result