import logging
import logging.config
import os
from datetime import datetime

from khp import utils
from pyfiglet import Figlet

FIGLET = Figlet(font='slant')

LOG = logging.getLogger(__name__)

CURR_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_DIR = os.path.join(CURR_DIR, 'config')
FTP_OUTPUT_DIR = os.path.join(CURR_DIR, 'output', 'ftp')
ICESCAPE_OUTPUT_DIR = os.path.join(CURR_DIR, 'output', 'icescape')
LOGGING_DIR = os.path.join(CURR_DIR, 'output', 'logs')

CONFIG_PATH = os.path.join(CONFIG_DIR, 'private.yml')
TRANSFORMS_PATH = os.path.join(CONFIG_DIR, 'transforms.yml')
LOGGING_PATH = os.path.join(CONFIG_DIR, 'logging.yml')

## Initialize logging
LOG_CONF = utils.read_yaml(LOGGING_PATH)
NOW = datetime.now().strftime('%Y-%m-%d %H:%M')
LOG_OUTPUT_FILE = os.path.join(LOGGING_DIR, NOW + '.txt')
LOG_CONF['handlers']['file']['filename'] = LOG_OUTPUT_FILE
logging.config.dictConfig(LOG_CONF)

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


def log_ascii():
    """Log the KHP ascii art
    """
    LOG.info('\n' + FIGLET.renderText("kid's help phone"))
