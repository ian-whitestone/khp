"""
Utils module, contains utility functions used throughout the codebase.
"""

import logging
import yaml
import os


log = logging.getLogger(__name__)

def read_yaml(yaml_file):
    """Read a yaml file.

    Args:
        yaml_file (str): Full path of the yaml file.

    Returns:
        data (dict): Dictionary of yaml_file contents.

    Raises:
        Exception: If the yaml_file cannot be opened.
    """

    try:
        log.debug("Reading in yaml file %s" % yaml_file)
        with open(yaml_file) as f:
            # use safe_load instead load
            data = yaml.safe_load(f)
        return data
    except Exception as e:
        log.error('Unable to read file %s. Error: %s' % (yaml_file,e))
        raise
