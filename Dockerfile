# docker file to setup badapple DBs (badapple_classic & badapple2 at time of writing)
# have to keep docker file in main dir (instead of under docker/) because
# docker-compose does not support subdirs when reading from git repositories

FROM ubuntu:22.04
WORKDIR /home/app
ENV DEBIAN_FRONTEND noninteractive

# Define required build-time arguments
ARG DB_PORT
ARG DB_NAME
ARG DB_USER
ARG DB_PASSWORD
ARG TZ
ARG PGDUMP_URL=${PGDUMP_URL}
ENV DB_PORT=${DB_PORT}
ENV DB_NAME=${DB_NAME}
ENV DB_USER=${DB_USER}
ENV DB_PASSWORD=${DB_PASSWORD}
ENV TZ=${TZ}
ENV PGDUMP_URL=${PGDUMP_URL}


RUN apt-get update
RUN echo "---Done installing Ubuntu."


WORKDIR /home/app

# Install necessary packages
RUN apt-get update && apt-get install -y \
    postgresql-14-rdkit \
    wget \
	tzdata \
	apt-utils \
	sudo \
    && rm -rf /var/lib/apt/lists/*
RUN echo "---Done installing packages"


# set timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ >/etc/timezone


# Copy configuration files and set appropriate permissions
COPY docker/config/postgresql/pg_hba.conf /etc/postgresql/14/main/
RUN chmod 640 /etc/postgresql/14/main/pg_hba.conf 
RUN chown postgres /etc/postgresql/14/main/pg_hba.conf 
COPY docker/config/postgresql/postgresql.conf /etc/postgresql/14/main/
RUN chmod 644 /etc/postgresql/14/main/postgresql.conf
RUN chown postgres /etc/postgresql/14/main/postgresql.conf
RUN echo "---Copied over PostgreSQL config files"


# update config file to use appropriate port
COPY docker/update_postgres_conf.sh /docker-entrypoint-initdb.d/update_postgres_conf.sh
RUN chmod +x /docker-entrypoint-initdb.d/update_postgres_conf.sh
RUN /docker-entrypoint-initdb.d/update_postgres_conf.sh
RUN echo "---Updated postgresql.conf to use correct port"


# download pgdump file
RUN wget -O /tmp/${DB_NAME}.pgdump ${PGDUMP_URL}
RUN echo "---Downloaded pgdump file"


# initialize DB
USER postgres
RUN pg_config
RUN /etc/init.d/postgresql start && \
	psql -p ${DB_PORT} -c "CREATE ROLE ${DB_USER} WITH LOGIN PASSWORD '${DB_PASSWORD}'" && \
	createdb -p ${DB_PORT} -O postgres ${DB_NAME} && \
	psql -p ${DB_PORT} -d ${DB_NAME} -c "CREATE EXTENSION rdkit" && \
	pg_restore -p ${DB_PORT} -O -x -v -d ${DB_NAME} /tmp/${DB_NAME}.pgdump && \
	psql -p ${DB_PORT} -d ${DB_NAME} -c "GRANT SELECT ON ALL TABLES IN SCHEMA public TO ${DB_USER}" && \
	psql -p ${DB_PORT} -d ${DB_NAME} -c "GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO ${DB_USER}" && \
	psql -p ${DB_PORT} -d ${DB_NAME} -c "GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO ${DB_USER}" && \
	psql -p ${DB_PORT} -l
USER root
RUN service postgresql stop
RUN echo "---Done instantiating and loading db."

# cleanup pgdump file
RUN rm /tmp/${DB_NAME}.pgdump

CMD ["sudo", "-u", "postgres", "/usr/lib/postgresql/14/bin/postgres", "-D", "/var/lib/postgresql/14/main", "-c", "config_file=/etc/postgresql/14/main/postgresql.conf"]