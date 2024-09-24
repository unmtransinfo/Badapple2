# based on: https://depth-first.com/articles/2010/02/08/big-data-in-chemistry-mirroring-pubchem-the-easy-way/

workdir="/media/jack/big_disk/data/pubchem"
ftp_directory="ftp.ncbi.nlm.nih.gov/pubchem/"

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
cd "$workdir" || exit

# Create necessary directories
mkdir -p "$ftp_directory"
mkdir -p Bioassay/CSV/Data/
mkdir -p Bioassay/Extras/

# Mount the FTP directory using curlftpfs
curlftpfs "$ftp_directory" "$ftp_directory" || { echo "Failed to mount FTP"; exit 1; }

# Sync files
sync_files "$ftp_directory" "Bioassay/CSV/Data/"
sync_files "$ftp_directory" "Bioassay/Extras/"

# Unmount the FTP directory
fusermount -u $ftp_directory
