FROM iskoldt/postgres16-rdkit:latest

# URL to the pgdump file
ARG PGDUMP_URL
ENV PGDUMP_URL=${PGDUMP_URL}

# database name
ARG POSTGRES_DB
ENV DB_NAME=${POSTGRES_DB}

# Install wget and download dump file at build time
RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*
RUN wget -O /tmp/restore.pgdump ${PGDUMP_URL}

# Copy restore script and make it executable
COPY restore.sh /docker-entrypoint-initdb.d/
RUN chmod +x /docker-entrypoint-initdb.d/restore.sh

# Document default port - note that this is determined by run-time env variable
EXPOSE 5432