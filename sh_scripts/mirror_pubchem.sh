# based on: https://depth-first.com/articles/2010/02/08/big-data-in-chemistry-mirroring-pubchem-the-easy-way/

if [ $# -lt 2 ]; then
	printf "Syntax: %s WORK_DIR FTP_DIR\n" $0
	exit
fi


WORK_DIR=$1
FTP_DIR=$2

# Function to sync files from FTP to local directory
sync_files() {
    local ftp_dir=$1
    local src_dir=$2

    if [ -d "$ftp_dir/$src_dir" ]; then
        rsync -r -t -v --progress --bwlimit=5000 --include='*.zip' --include='*.gz' --exclude='*' "$ftp_dir/$src_dir/" "$src_dir/"
    else
        echo "Source directory does not exist. Exiting."
        exit 1
    fi
}

# Change to the working directory
cd "$WORK_DIR" || exit

# Create necessary directories
mkdir -p "$FTP_DIR"
mkdir -p Bioassay/CSV/Data/
mkdir -p Bioassay/Extras/

# Mount the FTP directory using curlftpfs
curlftpfs "$FTP_DIR" "$FTP_DIR" || { echo "Failed to mount FTP"; exit 1; }

# Sync files
sync_files "$FTP_DIR" "Bioassay/CSV/Data/"
sync_files "$FTP_DIR" "Bioassay/Extras/"

# Unmount the FTP directory
fusermount -u $FTP_DIR
