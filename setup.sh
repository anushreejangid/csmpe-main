#!/bin/bash

set -e
virtualenv venv-csmpe
. venv-csmpe/bin/activate
wget --no-check-certificate https://raw.githubusercontent.com/anushreejangid/csmpe-main/master/setup.sh
pip install -r requirements.txt

