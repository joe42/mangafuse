#!/bin/bash
PYTHON_PCK_PATH="`python -c 'import cloudfusion; print cloudfusion.__file__'`"
CONFIG_DIR=`dirname "$PYTHON_PCK_PATH"`"cloudfusion/cloudfusion/config"

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
