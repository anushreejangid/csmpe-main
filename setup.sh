#!/bin/bash

set -e
virtualenv venv-csmpe
. venv-csmpe/bin/activate
wget --no-check-certificate https://github.com/anushreejangid/csmpe-main/blob/master/requirements.txt
pip install -r requirements.txt

