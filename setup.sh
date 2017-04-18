#!/bin/bash

set -e
virtualenv venv-csmpe
. venv-csmpe/bin/activate
wget --no-check-certificate https://raw.githubusercontent.com/anushreejangid/csmpe-main/master/requirements.txt -O requirements.txt
pip install -r requirements.txt

