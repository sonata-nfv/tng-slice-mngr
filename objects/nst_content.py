#!/usr/bin/python

class nst_content:
    def __init__(self):
        self.id = ""                      #id given by the creator of the slice
        self.name = ""
        self.version = ""
        self.author = ""
        self.vendor = ""
        self.nstNsdIds = []
        self.onboardingState = ""         #values are ENABLED/DISABLED in string format
        self.operationalState = ""        #values are ENABLED/DISABLED in string format
        self.usageState = ""              #values are IN_USE/NOT_IN_USE in string format
        self.notificationTypes = ""       #containts a Nst_Onboarding_Notification
        self.userDefinedData = ""

    def getID(self):
        return self.id

    def getName(self):
        return self.name

    def getVersion(self):
        return self.version

    def getAuthor(self):
        return self.author
    
    def getVendor(self):
        return self.vendor

    def getNsdIds(self):
        return self.nstNsdIds

    def getOnboardingState(self):
        return self.onboardingState

    def getOperationalStat(self):
        return self.operationalState

    def getUsageState(self):
        return self.usageState

    def getNorificationTypes(self):
        return self.notificationTypes

    def getUserDefinedData(self):
        return self.userDefinedData