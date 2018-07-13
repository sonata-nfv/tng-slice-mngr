[![Build Status](https://jenkins.sonata-nfv.eu/buildStatus/icon?job=tng-slice-mngr/master)](https://jenkins.sonata-nfv.eu/job/tng-slice-mngr/master)
[![Join the chat at https://gitter.im/5gtango/tango-schema](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/5gtango/tango-schema)

<p align="center"><img src="https://github.com/sonata-nfv/tng-api-gtw/wiki/images/sonata-5gtango-logo-500px.png" /></p>

# tng-slicemgr
- Description: 5GTANGO Service Platform Slice Manager
- Version: 1.0
- Features:
  · Network Slice Tempalte Management (create, check, update, delete).
  · Network Slice Instatiation Management (create, check, update, terminate).


## Required 5GTango components
- tng-rep
- tng-cat
- tng-gtk-common
- tng-gtk-sp


## Dependencies' version
This component is using the following dependencies. To be sure the code works, please use the following versions:
- Flask>=0.12.2
- flask-restful
- python-dateutil
- python-uuid
- requests
- xmlrunner==1.7.7

**NOTE:** these are minimum versions, it is not tested with the newest versions. probably they should be fine.


## License

This 5GTANGO component is published under Apache 2.0 license. Please see the LICENSE file for more details.


---
## Authors contact
  * Ricard Vilalta (ricard.vilalta@cttc.es)
  * Pol Alemany (pol.alemany@cttc.cat)
