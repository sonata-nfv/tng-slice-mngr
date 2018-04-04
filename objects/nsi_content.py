#!/usr/bin/python

class nsi_content:
    def __init__(self):
        self.nsiId=""
        self.nsiName=""
        self.nsiDescription=""
        self.nstId=""
        self.nstInfoId=""
        self.flavorId=""
        self.sapInfo=""
        self.nsiState=""
        self.instantiateTime=""
        self.terminateTime=""
        self.scaleTime=""
        self.updateTime=""
        self.uuidService=""
        
        
    def getID(self):
        return self.nsiId

    def getName(self):
        return self.nsiName

    def getDescription(self):
        return self.nsiDescription

    def getNSTId(self):
        return self.nstId

    def getInfoId(self):
        return self.nstInfoId

    def getFlavorIds(self):
        return self.flavorId

    def getSapInfo(self):
        return self.sapInfo

    def getNSIState(self):
        return self.nsiState
    
    def getInstatiateTime(self):
        return self.instantiateTime
    
    def getTerminateTime(self):
        return self.terminateTime
    
    def getScaleTime(self):
        return self.scaleTime
    
    def getUpdateTime(self):
        return self.updateTime
        
    def getUuidService(self):
        return self.uuidService