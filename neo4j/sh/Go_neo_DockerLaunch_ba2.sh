#!/bin/bash
###
# Script to install and run Neo4j via Docker, with APOC tools.
# See https://hub.docker.com/_/neo4j/
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
DOCKER_NEO_DATADIR=$(cd $HOME/../data/neo4j/data; pwd)
#
docker pull neo4j
#
(cd $HOME/neo4j/plugins ; wget https://github.com/neo4j-contrib/neo4j-apoc-procedures/releases/download/5.26.0/apoc-5.26.0-extended.jar)
#
docker run -d \
	-e NEO4J_dbms_security_procedures_unrestricted=apoc.\\\* \
	--publish=7474:7474 --publish=7687:7687 \
	--volume=$DOCKER_NEO_DATADIR:/data \
	neo4j
#
DOCKER_NEO4J_CID=$(docker container ls |grep neo4j |awk '{print $1}')
#
printf "DOCKER_NEO4J_CID: ${DOCKER_NEO4J_CID}\n"
#
docker container cp $HOME/neo4j/plugins/apoc-5.26.0-extended.jar $DOCKER_NEO4J_CID:/var/lib/neo4j/plugins
#
#
#docker exec $DOCKER_NEO4J_CID cp /var/lib/neo4j/labs/apoc-5.25.1-core.jar /var/lib/neo4j/plugins/
#
set -x
docker container stop $DOCKER_NEO4J_CID 
sleep 5
docker container start $DOCKER_NEO4J_CID 
set +x
#
# docker container rm $DOCKER_NEO4J_CID 
#
MessageBreak "DONE $(basename $0)"
#
