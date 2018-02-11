import logging
import utils
import os

log = logging.getLogger(__name__)

CURR_DIR = os.getcwd()
CONFIG_PATH = os.path.join(CURR_DIR, 'private.yml')
OUTPUT_DIR = os.path.join(CURR_DIR, 'output')

# read in private.yml
CONFIG = utils.read_yaml(CONFIG_PATH)

# timezone of the system the program is running on
SYS_TIMEZONE = "US/Eastern"
# timezone of the Icescape API
API_TIMEZONE = "UTC"
