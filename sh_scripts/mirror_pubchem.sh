# based on: https://depth-first.com/articles/2010/02/08/big-data-in-chemistry-mirroring-pubchem-the-easy-way/

workdir="/media/jack/big_disk/data/pubchem"
cd $workdir || exit

# Create necessary directories
mkdir -p ftp.ncbi.nlm.nih.gov/pubchem
mkdir -p bioassay

# Mount the FTP directory using curlftpfs
curlftpfs ftp.ncbi.nlm.nih.gov/pubchem/ ftp.ncbi.nlm.nih.gov/pubchem/ || { echo "Failed to mount FTP"; exit 1; }

# Check if the directory exists before rsync
if [ -d "ftp.ncbi.nlm.nih.gov/pubchem/Bioassay/CSV/Data" ]; then
    rsync -r -t -v --progress --bwlimit=500 --include='*/' --include='*.zip' --exclude='*' ftp.ncbi.nlm.nih.gov/pubchem/Bioassay/CSV/Data/ bioassay/
else
    echo "Source directory does not exist. Exiting."
    exit 1
fi

# Unmount the FTP directory
fusermount -u ftp.ncbi.nlm.nih.gov/pubchem/