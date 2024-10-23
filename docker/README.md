# Docker
This subdirectory contains docker files that can be used to setup the DBs locally (/for development) through docker. Instructions for setting up each DB using docker are provided below.

## Requirements
You will need to install docker on your machine. See the following URL for more information:
https://docs.docker.com/engine/install/ 


## badapple_classic
1. (Optional) modify the `.env_BA_classic` file to your desired requirements. 
2. The badapple_classic DB can be setup using the following command:
```
docker-compose --env-file .env_BA_classic -f compose_BA_classic.yml up --build -d
```
3. You can test that the DB is accessible using the following command (adjust the user/port if you've changed them):
```
psql -d badapple_classic -p 5443 -U robin -h localhost
```


## Notes:
* Depending on your version of docker, you may need to use `docker compose` instead of `docker-compose`
* Although generally it is best practice to use docker secrets for DB_PASSWORD, since these databases have intentionally been made completely public it is unnecessary in this case. The password is really just a config detail rather than security measure here.