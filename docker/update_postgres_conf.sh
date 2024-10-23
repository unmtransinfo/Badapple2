#!/bin/bash

# this file is for setting the port variable in postgresql.conf to what the user
# has defined in their .env file.
# used within docker container (does not modify outside files)

if [ -z "$DB_PORT" ]; then
  echo "DB_PORT is not set. Exiting."
  exit 1
fi

CONF_FILE="/etc/postgresql/14/main/postgresql.conf"
if [ ! -f "$CONF_FILE" ]; then
  echo "Configuration file not found at $CONF_FILE. Exiting."
  exit 1
fi

# modify the port in postgresql.conf
sed -i "s/^#*port = .*/port = $DB_PORT/" "$CONF_FILE"
echo "Updated postgresql.conf with port = $DB_PORT"