#!/bin/bash

wget https://github.com/joe42/mangafuse/raw/master/python-cloudfusion_0.5.0-1_all.deb -O /tmp/python-cloudfusion_0.5.0-1_all.deb
wget http://ftp.br.debian.org/debian/pool/main/p/python-poster/python-poster_0.8.1-0.1_all.deb -O /tmp/python-poster_0.8.1-0.1_all.deb


if [ "`id -u`" != "0" ]; then
  echo "Please, type root's password..."
  if [ `which sudo > /dev/null` ]; then
    
    sudo "dpkg -i /tmp/python-cloudfusion_0.5.0-1_all.deb /tmp/python-poster_0.8.1-0.1_all.deb"
  else
    su -c "gdebi /tmp/python-cloudfusion_0.5.0-1_all.deb /tmp/python-poster_0.8.1-0.1_all.deb"
  fi
fi
rm python-poster_0.8.1-0.1_all.deb python-cloudfusion_0.5.0-1_all.deb
