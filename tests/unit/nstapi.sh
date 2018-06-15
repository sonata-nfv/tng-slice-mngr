#!/bin/bash

docker run -i \
--network-alias=tng-slice-mngr \
--rm=true \
-v "$(pwd)/spec/reports/tng-slice-mngr:/code/log" \
registry.sonata-nfv.eu:5998/tng-slice-mngr python unit_nst_test.py
