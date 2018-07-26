[![Build Status](https://jenkins.sonata-nfv.eu/buildStatus/icon?job=tng-slice-mngr/master)](https://jenkins.sonata-nfv.eu/job/tng-slice-mngr/master)
[![Join the chat at https://gitter.im/sonata-nfv/](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/sonata-nfv/)

<p align="center"><img src="https://github.com/sonata-nfv/tng-api-gtw/wiki/images/sonata-5gtango-logo-500px.png" /></p>

# tng-slice-mngr
* Description: 5GTANGO Service Platform Slice Manager
* Version: 1.0
* Features:
    * Network Slice Tempalte Management (create, check, update, delete).
    * Network Slice Instantiation Management (create, check, update, terminate).

## Network Slice Theory
A Network Slice Instance (NSI) is defined in by Mschner K. et all Hedmar, P. in _Description of network slicing concept._ (NGMN  Alliance  document, January 2016) as a set of network functions and the resources for these network functions which are arranged and configured, forming a complete logical network, which meets certain characteristics in terms of available bandwidth, latency, or QoS, among others described in 5QI (5G QoS Indicator). Our component follows ETSI EVE 012 approach to combine 3GPP Network Slices and ETSI NFV network services. More information is provided at the wiki.

## Network Slice Manager Information
Here there is the documentation about the Network Slice Manager module belonging to SONATA (by 5GTango), both in terms of its internal design and usage.

### Component Design
This component is design with two main components:
* **Slice Lifecycle Manager:** It is the responsible for the entire lifecycle management of the created network slice instance, until it is terminated. Subsequent lifecycle events are likely to have an impact on the lifecycle of the underlying NSs, but not systematically. The Slice Lifecycle Manager  function  is  responsible  for  the  definition  and  update  of  Network Slice Templates (NST).

* **Slice2NS Mapper:** This component has to maintain an association between NST and NSDs identifiers, as well as an association between slice identifiers and NS instance identifiers.  In next releases, it might also deal with the required combination/integration/concatenation of NSs.
This behaviour might involve automatic generation of a new NSD, which might be explored in future releases. Slice2NS Mapper is responsible for interacting with SP MANO Framework.

### Basic API information
Each boject has its API definition, here we present the basic information but please reffer to the wiki pages for each object for further information on how to use the API.

#### Network Slice Template APIs
Available OpenAPI description: [slice-mngr_NST.json](https://github.com/rvilalta/tng-slice-mngr/blob/master/doc/slice-mngr_NST.json)

| Action  | HTTP method  | Endpoint |
|---|---|---|
| CREATE NST  | POST  | /api/nst/v1/descriptors  |
| GET ALL NST  | GET  | /api/nst/v1/descriptors  |
| GET SPECIFIC NST  | GET  | /api/nst/v1/descriptors/{nst_uuid}|
| DELETE NST  | DELETE  | /api/nst/v1/descriptors/{nst_uuid}|

#### Network Slice Instance APIs
Available OpenAPI description: [slice-mngr_NSI.json](https://github.com/rvilalta/tng-slice-mngr/blob/master/doc/slice-mngr_NSI.jsonn)

| Action  | HTTP method  | Endpoint |
|---|---|---|
| CREATE NSI  | POST  | /api/nsilcm/v1/nsi |
| GET ALL NSIs  | GET  | /api/nsilcm/v1/nsi  |
| GET SPECIFIC NSI  | GET  | /api/nsilcm/v1/nsi/{nsi_uuid}|
| TERMINATE NST  | DELETE  | /api/nsilcm/v1/nsi/{nsi_uuid}/terminate|


## Development
To contribute to the development of this 5GTANGO component, you may use the very same development workflow as for any other 5GTANGO Github project. That is, you have to fork the repository and create pull requests.

## Setup a Network Slice manager
### Dependencies
This component is using the following dependencies. To be sure the code works, please use the following versions:
* Flask (0.12.2)
* flask-restful
* python-dateutil
* python-uuid
* requests
* xmlrunner (1.7.7)

**NOTE:** these are minimum versions, it is not tested with the newest versions probably they should be fine. If there's no specific version, the newest versions should work fine but it is not tested.

### Required 5GTango components
To use this component it is necessary to install the following 5GTango components
* tng-rep
* tng-cat
* tng-gtk-common
* tng-gtk-sp (optional if you want to use "Emulation Mode", reffer to the wiki for further information).

### Installation
Once the previous components are installed, please execute the DockerFile of this component and eveything will be setup inside the used Docker.

To launch the service standalone, simply go to the main folder and execute this command: _python3 main.py_

### Usage
Please, access the wiki page of this repository for further information on how to "play" with the Network Slice Manager. 


## License
This 5GTANGO component is published under Apache 2.0 license. Please see the [LICENSE](https://github.com/sonata-nfv/tng-slice-mngr/blob/master/LICENSE) file for more details.

## Authors contact
  * Ricard Vilalta (ricard.vilalta@cttc.es)
  * Pol Alemany (pol.alemany@cttc.cat)
  
### Feedback-Chanel
* Please use the GitHub issues to report bugs.
