#!/bin/bash

docker run -i \
--rm=true \
-v "$(pwd)/spec/reports/tng-slice-mngr:/code/log" \
registry.sonata-nfv.eu:5000/tng-slice-mngr python /tng-slice-mngr/tests/unit/unit_nsi_test.py