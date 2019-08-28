[![Build Status](https://jenkins.sonata-nfv.eu/buildStatus/icon?job=tng-slice-mngr/master)](https://jenkins.sonata-nfv.eu/job/tng-slice-mngr/master)
[![Join the chat at https://gitter.im/sonata-nfv/](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/sonata-nfv/)

<p align="center"><img src="https://github.com/sonata-nfv/tng-api-gtw/wiki/images/sonata-5gtango-logo-500px.png" /></p>

# tng-slice-mngr
* Description: 5GTANGO Service Platform Slice Manager
* Version: 2.0
* Actions:
    * Network Slice Tempalte Management (create, check, update, delete).
    * Network Slice Instantiation Management (create/instantiate, check, update, terminate, delete).

## Network Slice Theory
A Network Slice Instance (NSI) is defined in by Mschner K. et all Hedmar, P. in _Description of network slicing concept._ (NGMN  Alliance  document, January 2016) as a set of network functions and the resources for these network functions which are arranged and configured, forming a complete logical network, which meets certain characteristics in terms of available bandwidth, latency, or QoS, among others described in 5QI (5G QoS Indicator). Our component follows ETSI EVE 012 approach to combine 3GPP Network Slices and ETSI NFV network services. More information is provided at the wiki.
* Features:
    * Network Slice Service Composition: link all the Networks Services within a Netwrok Slice
    * Network Slice Service Sharing: Share Network Services among Network Slices

## Network Slice Manager Information
Here there is the documentation about the Network Slice Manager module belonging to SONATA (by 5GTango), both in terms of its internal design and usage.

### Component Design
<p align="center"><img src="https://github.com/rvilalta/tng-slice-mngr/blob/master/doc/images/architecture.JPG" /></p>

This component is design with two main components:
* **Slice Lifecycle Manager:** It is the responsible for the entire lifecycle management of the created network slice instance, until it is terminated. Subsequent lifecycle events are likely to have an impact on the lifecycle of the underlying NSs, but not systematically. The Slice Lifecycle Manager  function  is  responsible  for  the  definition  and update of Network Slice Templates (NST).

* **Slice2NS Mapper:** This component has to maintain an association between NST and NSDs identifiers, as well as an association between slice identifiers and NS instance identifiers. Slice2NS Mapper is responsible for interacting with SP MANO Framework.

### Basic API information
Each SONATA component has its API definition, the next sub-setions present a basic **tng-slice-mngr** API information. Further information about the 5GTANGO software, click in the [Global SONATA API Webpage](https://sonata-nfv.github.io/tng-doc/?urls.primaryName=5GTANGO%20SDK%20Packager%20API%20v1).

#### Network Slice Template APIs
Available OpenAPI description: [slice-mngr_NST.json](https://github.com/sonata-nfv/tng-slice-mngr/blob/master/doc/v1_2/slice-mngr_NST.json)

| Action  | HTTP method  | Endpoint |
|---|---|---|
| CREATE NST  | POST  | /api/nst/v1/descriptors  |
| GET ALL NST  | GET  | /api/nst/v1/descriptors  |
| GET SPECIFIC NST  | GET  | /api/nst/v1/descriptors/{nst_uuid}|
| DELETE NST  | DELETE  | /api/nst/v1/descriptors/{nst_uuid}|

#### Network Slice Instance APIs
Available OpenAPI description: [slice-mngr_NSI.json](https://github.com/sonata-nfv/tng-slice-mngr/blob/master/doc/v1_2/slice-mngr_NSI.json)

| Action  | HTTP method  | Endpoint |
|---|---|---|
| CREATE/INSTANTIATE NSI  | POST  | /api/nsilcm/v1/nsi |
| GET ALL NSIs  | GET  | /api/nsilcm/v1/nsi  |
| GET SPECIFIC NSI  | GET  | /api/nsilcm/v1/nsi/{nsi_uuid} |
| TERMINATE NSI  | POST  | /api/nsilcm/v1/nsi/{nsi_uuid}/terminate |
| DELETE NSI | DELETE | /api/nsilcm/v1/nsi/{nsi_uuid} |


## Development
To contribute to the development of this 5GTANGO component, you may use the very same development workflow as for any other 5GTANGO Github project:
1) you have to fork the repository and create pull requests.
2) you pull requests will be verified and merged once a reviewer accepts it.

## Setup a Network Slice manager
### Dependencies
As the SONATA Service Platform is composed by multiple modules and all of them using Dockers, the 5GTANGO Network Slice Manager environment and its dependencies are already installed within the Docker. Just to inform about it, this component uses the following dependencies:
* Flask (0.12.2)
* flask-restful
* python-dateutil
* python-uuid
* requests
* xmlrunner (1.7.7)

**INFORMATION NOTE:** these are minimum versions, it is not tested with the newest versions probably they should be fine. If there's no specific version, the newest versions should work fine but it is not tested.

### Required 5GTango components
In order to have a full functionality, it is necessary to install the whole SP modules.

### Installation & Usage
In order to install this component, please follow the procedure described in the official [5GTango](https://5gtango.eu/software/documentation.html) Documentation webpage.

To use the SONATA Network Slice Manager feature, there are two possible options:
* [GUI (tng-portal)](https://github.com/sonata-nfv/tng-portal)
* [CLI (tng-cli)](https://github.com/sonata-nfv/tng-cli)

**INFORMATION NOTE**: Once installed (together with the SP modules) and before using it, if you are new on the Network Slicing "world", please check the information about the available functionalities accessing the [tng-slice-mngr wiki page](https://github.com/sonata-nfv/tng-slice-mngr/wiki).

## License
This 5GTANGO component is published under Apache 2.0 license. Please see the [LICENSE](https://github.com/sonata-nfv/tng-slice-mngr/blob/master/LICENSE) file for more details.

## Authors contact
  * Ricard Vilalta (ricard.vilalta@cttc.es)
  * Pol Alemany (pol.alemany@cttc.cat)
  
### Feedback-Chanel
* Please use the GitHub issues and the 5GTANGO development mailing list sonata-dev@lists.atosresearch.eu for feedback.
