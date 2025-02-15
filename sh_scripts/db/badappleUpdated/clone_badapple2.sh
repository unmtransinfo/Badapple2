# Script to clone badapple2DB
if [ $# -lt 2 ]; then
	printf "Syntax: %s DB_USER NEW_DB_NAME\n" $0
	exit
fi
DB_USER=$1
NEW_DB_NAME=$2

psql -d postgres -c "CREATE DATABASE $NEW_DB_NAME WITH TEMPLATE badapple2 OWNER $DB_USER;"
