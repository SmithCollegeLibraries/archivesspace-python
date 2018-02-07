#!/bin/bash

cd sphinx
make html text
cp -a _build/html/* ../docs/
