# Docker
This README provides instructions for setting up each DB using docker.

## Requirements
You will need to install docker on your machine. See the following URL for more information:
https://docs.docker.com/engine/install/ 


## badapple_classic
1. (Optional) modify the `.env_BA_classic` file to your desired requirements. 
    * Note: If you want to include the "activity" table in the DB, then change `PGDUMP_URL` to "https://unmtid-dbs.net/download/Badapple2/badapple_classic_full.pgdump"
2. The badapple_classic DB can be setup using the following command:
```
docker-compose --env-file ./docker/.env_BA_classic -f compose_BA_classic.yml up --build -d
```
3. You can test that the DB is accessible using the following command (adjust the user/port if you've changed them):
```
psql -d badapple_classic -p 5443 -U robin -h localhost
```

## badapple2
1. (Optional) modify the `.env_BA2` file to your desired requirements. 
    * Note: If you want to include the "activity" table in the DB, then change `PGDUMP_URL` to "https://unmtid-dbs.net/download/Badapple2/badapple2_full.pgdump"
2. The badapple2 DB can be setup using the following command:
```
docker-compose --env-file ./docker/.env_BA2 -f compose_BA2.yml up --build -d
```
3. You can test that the DB is accessible using the following command (adjust the user/port if you've changed them):
```
psql -d badapple2 -p 5443 -U frog -h localhost
```


## Notes:
* Depending on your version of docker, you may need to use `docker compose` instead of `docker-compose`
* Although generally it is best practice to use docker secrets for DB_PASSWORD, since these databases have intentionally been made completely public it is unnecessary in this case. The password is really just a config detail rather than security measure here.
* Dockerfiles are kept under the Badapple2/ directory (rather than Badapple2/docker/) directory because docker compose cannot use subdirectories as context w/ a GitHub repo (at the time of writing).