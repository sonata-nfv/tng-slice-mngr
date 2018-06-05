#!/usr/bin/python

class nst_content:
    def __init__(self):
        #self.id = ""                      #given by the catalogues
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