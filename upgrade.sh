#!/bin/bash
cd /home/obezpalko/src/4k
. ./4k/bin/activate
pip install --upgrade git+https://github.com/obezpalko/4k.git@stable
pip install --editable .

