#!/bin/bash
set -x

ncat -l -k -p 9000 --exec "/home/ubuntu/tsx/scripts/nc_handler.sh"