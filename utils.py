"""
Utils module, contains utility functions used throughout the codebase.
"""

import logging
import yaml
import os
import boto3
import pytz
import dateutil.parser
from datetime import datetime, timedelta, date

log = logging.getLogger(__name__)

def yesterdays_range():
    """Generate yesterdays date range, in datetime objects

    Returns:
        dt1 (datetime.datetime): Beginning of yesterday
        dt2 (datetime.datetime): End of yesterday
    """
    dt1 = datetime.now() - timedelta(1)
    dt1 = dt1.replace(hour=0, minute=0, second=0, microsecond=0)
    dt2 = dt1 + timedelta(hours=23, minutes=59, seconds=59, milliseconds=999)
    log.info("Yesterday's range start: {} end: {}".format(dt1, dt2))
    return dt1, dt2

def check_response(response):
    """Check the status of a requests response. If the status code is not 200,
    log the error and raise an exception.

    Args:
        response (requests.models.Response): Requests response object

    Raises
        Exception: If the status code is not 200
    """
    # TODO: implement
    if response.status_code == 200:
        return
    else:
        log.error("Requests error code: {0}. Response:\n{1}".format(
            response.status_code, response.text))
        raise Exception("Non-200 status code returned")
    return

def parse_date(str_dt):
    """Convert a date string to a datetime object

    Args:
        str_dt (str): Date in any format excepted by dateutil.parser. WARNING:
            read the dateutil.parser docs before using to udnerstand default
            behaviour (i.e. how str_dt's like `2018` or `2` are handled)

    Returns:
        dt (datetime.datetime): Datetime object
    """
    log.info("Parsing '{}' into datetime object".format(str_dt))
    try:
        return dateutil.parser.parse(str_dt)
    except ValueError:
        raise
    except Exception:
        log.error("Unable to parse str_dt due to error.")
        raise

def convert_timezone(dt, tz1, tz2):
    """Convert a datetime object from one timezone to another timezone

    Args:
        dt (datetime.datime): Datetime object to convert
        tz1 (str): pytz acceptable timezone that dt is in
        tz1 (str): pytz acceptable timezone to conver to

    Returns:
        dt2 (datetime.datetime): Datetime object in timezone 2
    """
    log.info("Converting '{}' from timezone: '{}' to timezone '{}'".format(
                dt, tz1, tz2))
    timezones = pytz.all_timezones
    if tz1 not in timezones or tz2 not in timezones:
        raise Exception("Supplied timezone(s) not in pytz available timezones. "
                            "See pytz.all_timezones for available timezones")
    zone1 = pytz.timezone(tz1)
    zone2 = pytz.timezone(tz2)
    dt1 = zone1.localize(dt) # not sure how to deal with `is_dst` dynamically..
    dt2 = dt1.astimezone(zone2)
    return dt2

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

def get_s3_keys(s3_bucket, prefix=None):
    """Get a list of keys in an S3 bucket. Optionally specify a prefix to
    narrow down the keys returned.

    Args:
        s3_bucket (str): Name of the S3 bucket.
        prefix (str, optional): File prefix. Defaults to None.
    Returns:
        keys (list): List of keys in the S3 bucket.
    """
    keys = []
    s3 = boto3.client('s3')

    paginator = s3.get_paginator('list_objects_v2')
    filters = {'Bucket': s3_bucket}
    if prefix is not None:
        filters['Prefix'] = prefix
    page_iterator = paginator.paginate(**filters)

    for page in page_iterator:
        for obj in page['Contents']:
            keys.append(obj['Key'])
    return keys

def read_s3_file(s3_bucket, key):
    """Read the contents of an S3 object.

    Args:
        s3_bucket (str): Name of the S3 bucket.
        key (str): Name of the S3 object

    Returns:
        contents (str): Contents of S3 object
    """
    log.info("Reading {0} from S3 bucket: {1}".format(key, s3_bucket))
    s3 = boto3.resource('s3')
    obj = s3.Object(s3_bucket, key)
    contents = obj.get()['Body'].read().decode('utf-8')
    return contents

def parse_s3_contents(contents, delimiter, remove_dupes=False,
                        skip_first_line=False):
    """Read the contents of an S3 object into a list of lists.

    Args:
        contents (str): contents of an S3 object
        delimiter (str): delimiter to split the contents of each line with
        remove_dupes (bool, optional): ensure each line is unique. Defaults to
            False.
        skip_first_line (bool, optional): skip the first line of the S3 object.
            Defaults to False.

    Returns:
        parsed_contents (list): List of lists, where each tuple is the contents
            of a single line.
    """
    lines = [line for line in contents.split('\r\n') if line != '']
    if remove_dupes:
        lines = list(set(lines))
        print (lines)
    parsed_contents = [line.split(delimiter) for line in lines]
    if skip_first_line:
        parsed_contents = parsed_contents[1:]

    return parsed_contents

def search_path(path, prefix=None, filetypes=[]):
    """Search a path and return all the files. Optionally specify file prefixes
    and/or filetypes to narrow your criteria.

    Args:
        path (str): input path
        prefix (str, optional): File prefix. Defaults to None.
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
    for p in os.listdir(path):
        prefix_check = True
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
