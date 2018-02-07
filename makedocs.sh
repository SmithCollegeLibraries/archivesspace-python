#!/bin/bash

cd sphinx
rm _build/text/*
make html text
cp -a _build/html/* ../docs/
