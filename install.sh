#!/bin/bash
user="$1"

if [ "`id -u`" == "0" -a "$user" == "" ]; then
  echo Execute this script as normal user and not as root.
  exit
else
  if [ "`id -u`" != "0" ]; then
    echo "Please, type root's password..."
    if [ `which sudo > /dev/null` ]; then
      sudo "bash $0 "`id -un`
    else
      su -c "bash $0 "`id -un`
    fi
    exit
  fi
fi

apt-get install git libfuse-dev fuse-utils python-setuptools -y
chmod a+x /usr/bin/fusermount
chmod a+rw /dev/fuse
usermod -a -G fuse $user
git clone git://github.com/joe42/mangafuse.git
chown -R $user:$user mangafuse
cd mangafuse/cloudfusion/
python setup.py install
cp ~/start_mangafuse.sh /usr/bin/mangafuse
