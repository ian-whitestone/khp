import logging
import utils
import os

log = logging.getLogger(__name__)

CURR_DIR = os.getcwd()
CONFIG_PATH = os.path.join(CURR_DIR, 'private.yml')
TRANSFORMS_PATH = os.path.join(CURR_DIR, 'transforms.yml')
FTP_OUTPUT_DIR = os.path.join(CURR_DIR, 'output', 'ftp')
ICESCAPE_OUTPUT_DIR = os.path.join(CURR_DIR, 'output', 'icescape')

## LOAD YAML FILES
# read in private.yml
CONFIG = utils.read_yaml(CONFIG_PATH)
TRANSFORMS = utils.read_yaml(TRANSFORMS_PATH)

# timezone of the system the program is running on
SYS_TIMEZONE = "US/Eastern"
# timezone of the Icescape API
API_TIMEZONE = "UTC"


## Icescape API constants
MAX_RESULTS = 10000
