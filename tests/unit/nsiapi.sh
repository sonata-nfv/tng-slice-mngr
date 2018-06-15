#!/bin/bash

docker run -i \
--net=son-sp \        ##TODO: ???
--network-alias=tng-slice-mngr \
--rm=true \
-v "$(pwd)/spec/reports/son-gtklic:/code/log" \  ##TODO:???
registry.sonata-nfv.eu:5998/tng-slice-mngr python unit_nst_test.py