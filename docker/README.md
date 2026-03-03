# Docker

This README provides instructions for setting up each DB using docker.

Please note that these instructions are intended for local/development use. For using the DBs in a production environment, please see [Badapple2-API repo](https://github.com/unmtransinfo/Badapple2-API).

## Requirements

You will need to install docker on your machine. See the following URL for more information:
https://docs.docker.com/engine/install/

## badapple_classic

1. (Optional) modify the [.env_BA_classic](.env_BA_classic) file to your desired requirements.
   - Note: If you want to include the "activity" table in the DB, then change `IMAGE_TAG` to `badapple_classic-full`
   - The default Postgres settings are optimized for a 4-core system with 8GB of RAM and SSD storage. If you have more (or less) resources available, you can adjust the `PG_` settings to improve performance. You can use the [pgtune](https://pgtune.leopard.in.ua/) tool to generate new settings.
2. The badapple_classic DB can be setup using the following command:

```bash
docker compose --env-file .env_BA_classic -f compose_BA_classic.yml up -d
```

It will take a few minutes to download the DB dump and restore it. You can monitor the progress by inspecting the logs:

```bash
docker compose --env-file .env_BA_classic -f compose_BA_classic.yml logs -f
```

3. You can test that the DB is accessible using the following command (adjust the user/port if you've changed them):

```bash
psql -d badapple_classic -p 5442 -U robin -h localhost
```

4. To shut down and remove the DB, use the following command:

```bash
docker compose --env-file .env_BA_classic -f compose_BA_classic.yml down -v
```

## badapple2

1. (Optional) modify the [.env_BA2](.env_BA2) file to your desired requirements.
   - Note: If you want to include the "activity" table in the DB, then change `IMAGE_TAG` to `badapple2-full`
   - The default Postgres settings are optimized for a 4-core system with 8GB of RAM and SSD storage. If you have more (or less) resources available, you can adjust the `PG_` settings to improve performance. You can use the [pgtune](https://pgtune.leopard.in.ua/) tool to generate new settings.
2. The badapple2 DB can be setup using the following command:

```bash
docker compose --env-file .env_BA2 -f compose_BA2.yml up -d
```

It will take a few minutes to download the DB dump and restore it. You can monitor the progress by inspecting the logs:

```bash
docker compose --env-file .env_BA2 -f compose_BA2.yml logs -f
```

3. You can test that the DB is accessible using the following command (adjust the user/port if you've changed them):

```bash
psql -d badapple2 -p 5443 -U frog -h localhost
```

4. To shut down and remove the DB, use the following command:

```bash
docker compose --env-file .env_BA2 -f compose_BA2.yml down -v
```

## Notes:

- Depending on your version of docker, you may need to use `docker-compose` instead of `docker compose`
- Although generally it is best practice to use docker secrets for DB_PASSWORD, since:

1. The provided compose files are intended for local use
2. These databases have intentionally been made completely public

It is unnecessary in this case. The password is really just a config detail rather than security measure here.
