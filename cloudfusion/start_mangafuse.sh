#!/bin/bash
CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $CURRENT_DIR
mkdir -p ~/.mangas  .cloudfusion/logs
python -m cloudfusion.main  ~/.mangas 
cp cloudfusion/config/mangafuse.ini ~/mangas/data/config/config
mkdir  ~/.mangas/data/tower\ of\ god
if [ ! -h ~/mangas ]
then
	ln -sf ~/.mangas/data ~/mangas
fi
xdg-open ~/mangas
