#!/bin/bash
rm -rf venv-csmpe
virtualenv venv-csmpe && \
source venv-csmpe/bin/activate && \
wget --no-check-certificate https://raw.githubusercontent.com/anushreejangid/csmpe-main/master/requirements.txt -O requirements.txt && \
pip install -r requirements.txt

