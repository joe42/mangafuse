#!bin/bash
CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $CURRENT_DIR
mkdir ~/mangafuse 
python -m cloudfusion.main ~/mangafuse
cp cloudfusion/config/mangafuse.ini mnt/config/config

