# Badapple2
Bioassay data associative promiscuity pattern learning engine V2.

For general use cases one can use the Badapple2 webapp: https://chiltepin.health.unm.edu/badapple2 

If you would like to install Badapple locally and/or would like to use any of the code within this repository, please continue reading.

## badapple_classic
If you want to setup the badapple_classic DB follow the instructions [here](badapple1_comparison/README.md).

## badapple2
The steps below outline how one can setup the badapple2 DB.

### Easy Setup

#### Option 1: Docker
Use this option to install a Docker image with the DB.


See the docker README file [here](docker/README.md#badapple2)


#### Option 2: PostgreSQL
Use this option to install the DB directly on your system using PostgreSQL.

1. Follow the PostgreSQL setup instructions [here](#postgresql-setup)
2. Download [badapple2.pgdump](https://unmtid-dbs.net/download/Badapple2/badapple2.pgdump).
    * **Note:** If your use case needs the "activity" table, then instead download [badapple2_full.pgdump](https://unmtid-dbs.net/download/Badapple2/badapple2_full.pgdump)
3. Create the DB: `createdb badapple2`
3. Load DB from dump file: `pg_restore -O -x -v -d badapple2 badapple2.pgdump`
    * **Note:** If you're including the "activity" table then use: `pg_restore -O -x -v -d badapple2 badapple2_full.pgdump`

### Setup "from-scratch"
**You can skip this section if you setup the DB using the steps from above**

If you would like to run the entire workflow used to create the badapple2 DB, then please follow the instructions [here](snakemake/README.md)

## badapple_classic vs badapple2
Although badapple_classic and badapple2 have similar structure, the data within each is not identical. The most significant differences between badapple_classic and badapple2 are as follows:
* badapple_classic uses the same set of (823) assays as the original badapple DB, whereas badapple2 incorporates an additional 83 new assay records (906 total). 
    * For both cases, assay records are restricted to HTS (>= 20k compounds) and come from NIH centers.
    * You can compare the files [badapple_classic_tested.aid](https://unmtid-dbs.net/download/Badapple2/badapple_classic_files/badapple_classic_tested.aid) and [badapple2_tested.aid](https://unmtid-dbs.net/download/Badapple2/badapple2_files/badapple2_tested.aid) to see the exact difference.
* badapple_classic was restricted to substances from [MLSMR](https://pubchem.ncbi.nlm.nih.gov/source/MLSMR), whereas badapple2 uses all bioactivity data present in the provided assay records.
* In terms of pScores, badapple2 uses the badapple_classic medians to normalize scores in order to ensure that our criteria for what constitutes a "high" amounts of evidence remains consistent.
    * If you would like to view a detailed comparison of the pScores between badapple_classic and badapple2 please see [this notebook](src/notebooks/badapple2-vs-badapple_classic.ipynb).
    * Note that because we no longer use the MLSMR filter, there are many scaffolds present in badapple2 which have a low amount of evidence. Using the badapple2 medians to normalize scores would significantly lower the bar for what is considered enough evidence to assign a high pScore.

In addition to the items above, badapple2 stores information not present in badapple_classic, including:
* Biological target information for each assay
* A record of the specific approved drug(s) a scaffold is present in if `inDrug==True`
* Assay descriptors (description and protocol text + annotations from [BARD](https://pmc.ncbi.nlm.nih.gov/articles/PMC4383997/))

## Code Usage
If you'd like to run the scripts/code contained within this repository then you will need to follow the setup guidelines outlined below.

### System Requirements
Code is expected to work on Linux systems. 

MacOS and Windows users will need need to modify the conda [environment.yml](environment.yml) file. Make sure to follow appropriate installation guidelines for other dependencies (PostgreSQL, Docker). Please note that packages/dependencies may function differently across operating systems.

### Python Setup
1. Setup conda (see the [Miniconda Site](https://conda.github.io/conda-libmamba-solver/user-guide/) for more info) 
    * (Optional) I'd recommend using the libmamba solver for faster install times, see [here](https://conda.github.io/conda-libmamba-solver/user-guide/)
2. Install the Badapple2 environment: `conda env create -f environment.yml`
    * This will create a new conda env with name `badapple2`. If you wish, you can change the first line of [environment.yml](environment.yml) prior to the command above to change the name.


### PostgreSQL Setup
1. Install PostgreSQL with the RDKit cartridge (requires sudo):
`sudo apt install postgresql-14-rdkit`
2. (Option 1) Make your user a superuser prior to DB setup:
    1) Switch to postgres user: `(base) <username>@<computer>:~$ sudo -i -u postgres`
    2) Make yourself a superuser: `psql -c "CREATE ROLE <username> WITH SUPERUSER PASSWORD '<password>'"`
3. (Option 2) If you don't want to make `<username>` a superuser, follow the steps below:
    1) When running DB setup commands, prepend `sudo -u postgres` to DB setup commands. For example, instead of `createdb <DB_NAME>` use `sudo -u postgres createdb <DB_NAME>`.
    2) After setting up the DB as `postgres` you can grant permissions to `<username>` to access the DB as `<username>` like so:
    ```
    sudo -i -u postgres
    psql -d <DB_NAME> -c "CREATE ROLE <username> WITH LOGIN PASSWORD '<password>'"
    psql -d <DB_NAME> -c "GRANT SELECT ON ALL TABLES IN SCHEMA public TO <username>"
    psql -d <DB_NAME> -c "GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO <username>"
    psql -d <DB_NAME> -c "GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO <username>"
    ```