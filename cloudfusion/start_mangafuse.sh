#!bin/bash
CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $CURRENT_DIR
mkdir -p ~/.mangafuse  .cloudfusion/logs
python -m cloudfusion.main  ~/.mangafuse 
cp cloudfusion/config/mangafuse.ini mnt/config/config
mkdir  ~/.mangafuse/data/tower\ of\ god
if [ ! -h ~/mangafuse ]
then
	ln -sf ~/.mangafuse/data ~/mangafuse
fi
xdg-open ~/mangafuse
