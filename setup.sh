#!/bin/bash
rm -rf venv-csmpe
virtualenv venv-csmpe && \
( . venv-csmpe/bin/activate ) && \
(
if [[ "CSM$CSMPE_GITHUB" == "CSM" ]]; then
    wget --no-check-certificate https://raw.githubusercontent.com/anushreejangid/csmpe-main/master/requirements.txt -O requirements.txt
else
    wget --no-check-certificate http://gitlab.cisco.com/anjangid/csmpe-main/raw/master/setup.sh -O requirement.txt
fi
) && \
pip install -r requirements.txt

