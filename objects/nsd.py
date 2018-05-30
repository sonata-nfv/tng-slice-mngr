#!/usr/bin/python

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
        str_result =  "NSD: " + self.uuid \
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

  