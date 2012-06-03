#!/bin/bash
user="$1"

if [ "`id -u`" == "0" ]; then
  echo Execute this script as normal user and not as root.
  exit
else
  echo "Please, type root's password..."
  if [ `which sudo > /dev/null` ]; then
    sudo "bash $0 $@"
  else
    su -c "bash $0 $@"
  fi
fi

apt-get install git -y
apt-get install python-setuptools -y
git clone git://github.com/joe42/mangafuse.git
chown -R $user:$user mangafuse
cd mangafuse/cloudfusion/
python setup.py install
