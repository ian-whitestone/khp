# KHP
```
    __   _     ___          __         __               __
   / /__(_)___/ ( )_____   / /_  ___  / /___     ____  / /_  ____  ____  ___
  / //_/ / __  /|// ___/  / __ \/ _ \/ / __ \   / __ \/ __ \/ __ \/ __ \/ _ \
 / ,< / / /_/ /  (__  )  / / / /  __/ / /_/ /  / /_/ / / / / /_/ / / / /  __/
/_/|_/_/\__,_/  /____/  /_/ /_/\___/_/ .___/  / .___/_/ /_/\____/_/ /_/\___/
                                    /_/      /_/
```

Data infrastructure for the Kids Help Phone.

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