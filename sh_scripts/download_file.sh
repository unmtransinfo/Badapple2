# Author: Jack Ringer
# Date: 11/22/24
# Description: Simple script to download file from a given address and move
# the downloaded file to a destination directory.

if [ $# -lt 3 ]; then
	printf "Syntax: %s FILE_URL FILE_NAME DESTINATION_DIR\n" $0
	exit
fi

FILE_URL=$1
FILE_NAME=$2
DESTINATION_DIR=$3

wget -O $FILE_NAME $FILE_URL
mv $FILE_NAME $DESTINATION_DIR

