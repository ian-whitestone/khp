"""
Utils module, contains utility functions used throughout the codebase.
"""

import logging
import yaml
import os
import boto3


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

def upload_to_s3(s3_bucket, files):
    """Upload a list of files to S3.

    Args:
        s3_bucket (str): Name of the S3 bucket.
        files (list): List of files to upload
    """
    log.info("Attempting to load {0} files to s3 bucket: {1}".format(
                len(files), s3_bucket))
    s3 = boto3.resource('s3')
    for f in files:
        data = open(f, 'rb')
        s3.Bucket(s3_bucket).put_object(Key=os.path.basename(f), Body=data)

def get_s3_keys(s3_bucket):
    """Get a list of keys in an S3 bucket.

    Args:
        s3_bucket (str): Name of the S3 bucket.

    Returns:
        keys (list): List of keys in the S3 bucket.
    """
    keys = []
    s3 = boto3.client('s3')
    resp = s3.list_objects_v2(Bucket=s3_bucket)
    for obj in resp['Contents']:
        keys.append(obj['Key'])
    return keys


def search_path(path, prefix=None, filetypes=[]):
    """Search a path and return all the files. Optionally specify file prefixes
    and/or filetypes to narrow your criteria.

    Args:
        path (str): input path
        prefix (str, optional): File prefix
        filetypes (list, optional): List of file types to search for
            (i.e. ['.xls', '.xlsx', '.pdf'])

    Returns:
        files (list): list of files matching the specified filetypes
    """
    files = []
    log.info('Searching for files in %s' % path)
    for p in os.listdir(path):
        fullPath = os.path.join(path, p)

        type_check = True
        prefix_check = True
        if os.path.isfile(fullPath):
            basename = os.path.basename(fullPath)
            if filetypes:
                type_check = fullPath.endswith(tuple(filetypes))
            if prefix:
                prefix_check = basename.startswith(prefix)
            if type_check and prefix_check:
                files.append(fullPath)
    log.info("Found {0} files in {1} matching prefix '{2}' and filetypes {3}"
                .format(len(files), path, prefix, filetypes))
    return files

def clean_dir(path, prefix=None):
    """Helper function to clear any folders and files in a specified path.

    Args:
        path (str): input path
        prefix (str, optional): File prefix
    """
    log.info("Cleaning folders in %s" % path)
    prefix_check = True
    for p in os.listdir(path):
        fullPath = os.path.join(path, p)
        if os.path.isdir(fullPath):
            shutil.rmtree(fullPath)
            assert not os.path.isdir(fullPath)
            log.debug("Successfully removed folder " + fullPath)
        elif os.path.isfile(fullPath):
            basename = os.path.basename(fullPath)
            if prefix is not None:
                prefix_check = basename.startswith(prefix)
            if prefix_check and basename.startswith('.') == False:
                os.remove(fullPath)
                assert not os.path.isfile(fullPath)
                log.debug("Successfully removed file " + fullPath)
    return
