#!/bin/bash
###
# Script to transform Badapple Postgresql RDB to Neo4j GDB.
# Docker Neo4j server should be installed and running.
# See https://hub.docker.com/_/neo4j/
# docker pull neo4j
# docker run \
#   --publish=7474:7474 --publish=7687:7687 \
#   --volume=$HOME/neo4j/data:/data \
#   neo4j
###
#
function MessageBreak {
  printf "============================================\n"
  printf "=== [%s] %s\n" "$(date +'%Y-%m-%d:%H:%M:%S')" "$1"
}
#
T0=$(date +%s)
#
MessageBreak "STARTING $(basename $0)"
#
cwd=$(pwd)
#
NEO4J_HOST="localhost"
NEO4J_PORT="7687"
NEO4J_DATABASE="neo4j"
NEO4J_USERNAME="neo4j"
NEO4J_PASSWORD="neo4jjyang"
#
NEO4J_URL="bolt://${NEO4J_HOST}:${NEO4J_PORT}"
#
DOCKER_NEO4J_CID=$(docker container ls |grep neo4j |awk '{print $1}')
#
NEO_IMPORT_DIR="/var/lib/neo4j/import"
#
#
if [ "$(which cypher-shell)" ]; then
	CYSH="$(which cypher-shell)"
else
	echo "ERROR: cypher-shell not found."
	exit
fi
printf "CYSH = %s\n" "$CYSH"
#
DOCKER_DATADIR="$NEO_IMPORT_DIR/badapple"
docker exec $DOCKER_NEO4J_CID mkdir "$DOCKER_DATADIR"
docker exec $DOCKER_NEO4J_CID chown neo4j "$DOCKER_DATADIR"
docker exec $DOCKER_NEO4J_CID chmod g+w "$DOCKER_DATADIR"
#
#
./bac_export.sh
#
# Copy TSVs into Docker container:
DATADIR="$(cd $HOME/../data/Badapple/data/neo4j; pwd)"
docker container cp $DATADIR/scaffold.tsv $DOCKER_NEO4J_CID:$DOCKER_DATADIR
docker container cp $DATADIR/compound.tsv $DOCKER_NEO4J_CID:$DOCKER_DATADIR
docker container cp $DATADIR/scaf2cpd.tsv $DOCKER_NEO4J_CID:$DOCKER_DATADIR
docker container cp $DATADIR/scaf2scaf.tsv $DOCKER_NEO4J_CID:$DOCKER_DATADIR
###
# Perhaps "neo4j-admin import" would be faster?
#
#$CYSH "CALL db.constraints() YIELD name AS constraint_name DROP CONSTRAINT constraint_name"
#
# Delete all:
$CYSH -a neo4j://${NEO4J_HOST}:${NEO4J_PORT} -d ${NEO4J_DATABASE} -u ${NEO4J_USERNAME} -p ${NEO4J_PASSWORD} 'MATCH (n) DETACH DELETE n'
#
###
MessageBreak "LOAD NODES:"
$CYSH -a neo4j://${NEO4J_HOST}:${NEO4J_PORT} -d ${NEO4J_DATABASE} -u ${NEO4J_USERNAME} -p ${NEO4J_PASSWORD} <cql/load_main_node.cql
#
MessageBreak "LOAD EDGES:"
$CYSH -a neo4j://${NEO4J_HOST}:${NEO4J_PORT} -d ${NEO4J_DATABASE} -u ${NEO4J_USERNAME} -p ${NEO4J_PASSWORD} <cql/load_main_edge.cql
#
#$CYSH <cql/load_extras.cql
#$CYSH <cql/db_describe.cql
#
###
# Delete edges with:
# cypher-shell 'MATCH ()-[r]-() DELETE r'
# Delete all with:
# cypher-shell 'MATCH (n) DETACH DELETE n'
###
#
MessageBreak "DONE $(basename $0)"
#
