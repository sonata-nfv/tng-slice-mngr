#!/usr/bin/python

class nst_content:
    def __init__(self):
        self.id = ""
        self.nstId = ""
        self.nstName = ""
        self.nstVersion = ""
        self.nstDesigner = ""
        self.nstInvariantId = ""
        self.nstNsdIds = []
        self.nstOnboardingState = ""     #values are ENABLED/DISABLED in string format
        self.nstOperationalState = ""    #values are ENABLED/DISABLED in string format
        self.nstUsageState = ""          #values are IN_USE/OUT_USE (??) in string format
        self.notificationTypes = ""      #containts a Nst_Onboarding_Notification
        self.userDefinedData = ""

    def getID(self):
        return self.id

    def getnstID(self):
        return self.nstId

    def getName(self):
        return self.nstName

    def getVersion(self):
        return self.nstVersion

    def getDesigner(self):
        return self.nstDesigner

    def getInvariantId(self):
        return self.nstInvariantId

    def getNsdIds(self):
        return self.nstNsdIds

    def getOnboardingState(self):
        return self.nstOnboardingState

    def getOperationalStat(self):
        return self.nstOperationalState

    def getUsageState(self):
        return self.nstUsageState

    def getNorificationTypes(self):
        return self.notificationTypes

    def getUserDefinedData(self):
        return self.userDefinedData