# KHP

This repo is setup to pull down various reports from the KHP FTP server. These reports will then get loaded to a Postgres DB hosted on AWS RDS, for downstream consumption by numerous applications.

## FTP Servers

```python
from khp import ftp
from khp import config

## CSI Files
## Run every 10 minutes
download('CSI_files', config.FTP_OUTPUT_DIR)
load_to_s3("V1")

## FTCI Files
## Run twice per day
download('FTCI_files/Archive', config.FTP_OUTPUT_DIR)
load_to_s3("V2")
load_ftci_to_postgres()
```

## Icescape

```python
from khp import contacts

contacts.main()
```