"""
Utils module, contains utility functions used throughout the codebase.
"""

import logging
import yaml
import os
import boto3
import pytz
import re

import dateutil.parser
from datetime import datetime, timedelta, date
import json
import pandas as pd

LOG = logging.getLogger(__name__)

def chunker(seq, chunk_size):
    """Break a list into a set of smaller lists with len = chunk_size

    Args:
        seq (list): list to split up into chunks
        chunk_size (int): size of chunks

    Returns:
        list: list of lists with len = chunk_size
    """
    return (seq[pos:pos + chunk_size] for pos in
            range(0, len(seq), chunk_size))

def generate_date_range(start_date, end_date):
    """Generate the range of dates between start_date and end_date

    Args:
        start_date (str): Start date, `YYYY-mm-dd`
        end_date (str): End date, `YYYY-mm-dd`

    Returns:
        list: List of dates, as datetime.datetime objects, between start_date
            and end_date
    """
    pandas_range = list(pd.date_range(start_date, end_date))
    return [dt.to_pydatetime() for dt in pandas_range]

def read_jason(filename):
    """Read a json file into a python object

    Args:
        filename (str): path of the file

    Returns:
        list or dict: parsed data from the file
    """
    with open(filename, "r") as f:
        content = f.read()

    return json.loads(content)
def write_jason(data, filename):
    """Write a Python list or dictionary to a json file.

    Args:
        data (list or dict): data to write to file
        filename (str): path of the file to write to
    """
    LOG.info("Writing data as json to {}".format(filename))
    with open(filename, 'w') as outfile:
        json.dump(data, outfile)

def yesterdays_range():
    """Generate yesterdays date range, in datetime objects

    Returns:
        datetime.datetime: Beginning of yesterday
        datetime.datetime: End of yesterday
    """
    yesterday = datetime.now() - timedelta(1)
    start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(hours=23, minutes=59, seconds=59, milliseconds=999)
    LOG.info("Yesterday's range start: {} end: {}".format(start, end))
    return start, end

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
        LOG.error("Requests error code: {0}. Response:\n{1}".format(
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
        datetime.datetime: Datetime object
    """
    LOG.info("Parsing '{}' into datetime object".format(str_dt))
    try:
        return dateutil.parser.parse(str_dt)
    except ValueError:
        raise
    except Exception:
        LOG.error("Unable to parse str_dt due to error.")
        raise

def convert_timezone(dt, tz1, tz2):
    """Convert a datetime object from one timezone to another timezone

    Args:
        dt (datetime.datime): Datetime object to convert
        tz1 (str): pytz acceptable timezone that dt is in
        tz1 (str): pytz acceptable timezone to conver to

    Returns:
        datetime.datetime: Datetime object in timezone 2
    """
    LOG.info("Converting '{}' from timezone: '{}' to timezone '{}'".format(
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
        dict: Dictionary of yaml_file contents.

    Raises:
        Exception: If the yaml_file cannot be opened.
    """

    try:
        LOG.debug("Reading in yaml file %s" % yaml_file)
        with open(yaml_file) as f:
            # use safe_load instead load
            data = yaml.safe_load(f)
        return data
    except Exception:
        LOG.error('Unable to read file %s.' % (yaml_file))
        raise

def upload_to_s3(s3_bucket, files, encrypt=True):
    """Upload a list of files to S3.

    Args:
        s3_bucket (str): Name of the S3 bucket.
        files (list): List of files to upload
        encrypt (:obj:`bool`, optional): Use serverside AES256 encryption,
            defaults to True.
    """
    LOG.info("Attempting to load {0} files to s3 bucket: {1}".format(
             len(files), s3_bucket))
    s3 = boto3.resource('s3')
    for f in files:
        data = open(f, 'rb')
        if encrypt:
            s3.Bucket(s3_bucket).put_object(Key=os.path.basename(f), Body=data,
                                            ServerSideEncryption='AES256')
        else:
            s3.Bucket(s3_bucket).put_object(Key=os.path.basename(f), Body=data)

def get_s3_keys(s3_bucket, prefix=None):
    """Get a list of keys in an S3 bucket. Optionally specify a prefix to
    narrow down the keys returned.

    Args:
        s3_bucket (str): Name of the S3 bucket.
        prefix (:obj:`str`, optional): File prefix. Defaults to None.
    Returns:
        list: List of keys in the S3 bucket.
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
        str: Contents of S3 object
    """
    LOG.info("Reading {0} from S3 bucket: {1}".format(key, s3_bucket))
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
        remove_dupes (:obj:`bool`, optional): ensure each line is unique.
            Defaults to False.
        skip_first_line (:obj:`bool`, optional): skip the first line of the S3
            object. Defaults to False.

    Returns:
        list: List of lists, where each tuple is the contents of a single line.
    """
    lines = [line for line in contents.split('\r\n') if line != '']
    if remove_dupes:
        lines = list(set(lines))
        print (lines)
    parsed_contents = [line.split(delimiter) for line in lines]
    if skip_first_line:
        parsed_contents = parsed_contents[1:]

    return parsed_contents

def search_path(path, like=None):
    """Search a path and return all the files. Optionally specify file prefixes
    and/or filetypes to narrow your criteria.

    Args:
        path (str): input path
        like (:obj:`list`, optional): List of file regexes to match files on

    Returns:
        list: list of files matching the specified filetypes
    """
    files = []
    LOG.info('Searching for files in %s' % path)
    for p in os.listdir(path):
        full_path = os.path.join(path, p)

        if os.path.isfile(full_path):
            basename = os.path.basename(full_path)
            if like:
                matches = [(True if re.search(reg, basename) else False)
                           for reg in like]
                if sum(matches) > 0:
                    files.append(full_path)
            else:
                files.append(full_path)
    LOG.info("Found %s files in %s", len(files), path)
    return files

def clean_dir(path, prefix=None):
    """Helper function to clear any folders and files in a specified path.

    Args:
        path (str): input path
        prefix (:obj:`str`, optional): File prefix
    """

    LOG.info("Cleaning folders in %s" % path)
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
