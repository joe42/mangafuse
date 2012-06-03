#!/bin/bash
has_sudo=0
user=`id -nu`

if [ "`id -u`" == "0" ]; then
  echo Execute this script as normal user and not as root.
  exit
fi
if [ `which sudo > /dev/null` ]; then
  sudo su
else
  su
fi

apt-get install git -y
apt-get install python-setuptools -y
git clone git://github.com/joe42/mangafuse.git
chown -R $user:$user mangafuse
cd mangafuse/cloudfusion/
python setup.py install
