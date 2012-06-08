#!/bin/bash
PYTHON_PCK_PATH="`python -c 'import cloudfusion; print cloudfusion.__file__'`"
CONFIG_DIR=`dirname "$PYTHON_PCK_PATH"`"/config"

has_fuse_group="`id -Gn|grep " fuse "`"
if [ -n "$has_fuse_group" ]; then
	echo "Please, type root's password..."
	if [ `which sudo > /dev/null` ]; then
		sudo "usermod -a -G fuse "`id -un`
	else
		su -c "usermod -a -G fuse "`id -un`
	fi
	exit
fi
mkdir -p ~/.mangas  .cloudfusion/logs
python -m cloudfusion.main  ~/.mangas foreground >/dev/null 2>&1 &
sleep 1
cp "$CONFIG_DIR"/mangafuse.ini ~/.mangas/config/config
sleep 1
mkdir  ~/.mangas/data/tower\ of\ god
if [ ! -h ~/mangas ]
then
	ln -sf ~/.mangas/data ~/mangas
fi
xdg-open ~/mangas
