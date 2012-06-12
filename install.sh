#!/bin/bash

wget https://github.com/joe42/mangafuse/raw/master/python-cloudfusion_0.5.0-1_all.deb -O /tmp/python-cloudfusion_0.5.0-1_all.deb
if [ -n "`which gdebi`" ]; then
    gdebi /tmp/python-cloudfusion_0.5.0-1_all.deb 
else
    software-center /tmp/python-cloudfusion_0.5.0-1_all.deb 
fi
rm /tmp/python-cloudfusion_0.5.0-1_all.deb
