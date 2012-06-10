#!/bin/bash

wget https://github.com/joe42/mangafuse/raw/master/python-cloudfusion_0.5.0-1_all.deb -O /tmp/python-cloudfusion_0.5.0-1_all.deb
wget http://ftp.br.debian.org/debian/pool/main/p/python-poster/python-poster_0.8.1-0.1_all.deb -O /tmp/python-poster_0.8.1-0.1_all.deb
dpkg -i /tmp/python-cloudfusion_0.5.0-1_all.deb /tmp/python-poster_0.8.1-0.1_all.deb
rm /tmp/python-poster_0.8.1-0.1_all.deb /tmp/python-cloudfusion_0.5.0-1_all.deb
