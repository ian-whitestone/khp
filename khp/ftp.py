from datetime import datetime
import os
import logging

import postgrez
from khp import config
from khp import utils
from khp.implicity_tls import tyFTP

LOG = logging.getLogger(__name__)
CONF = config.CONFIG
S3_BUCKET = CONF['aws']['s3_bucket']

def download(folder, output_dir):
    """Download files from a folder within the KHP FTP server.

    Args:
        folder (str): folder to download files from
    """
    LOG.info('Downloading files from FTP folder %s', folder)
    ftp_conf = CONF['ftp']
    with tyFTP() as ftp:
        LOG.debug("Connecting to host %s", ftp_conf['host'])
        ftp.connect(host=ftp_conf['host'].encode("ascii"),
                        port=ftp_conf['port'])
        LOG.debug("Logging into host %s", ftp_conf['host'])
        ftp.login(user=ftp_conf['user'], passwd=ftp_conf['pwd'])
        LOG.debug("Switching to secure data connection")
        ftp.prot_p()
        ftp.cwd(folder)
        files = []
        ftp.retrlines("LIST", files.append)
        LOG.debug('%s files found in folder %s', len(files), folder)
        for ftp_file in files:
            words = ftp_file.split(None, 8)
            filename = words[-1].lstrip()
            LOG.debug("Writing file %s" % filename)
            output_file = os.path.join(output_dir, filename)
            with open(output_file, "wb") as f:
                ftp.retrbinary("RETR " + filename, f.write, 8*1024)

def load_to_s3(prefix=None):
    """Load the downloaded files to S3, that have not already been uploaded.
    Optionally specify a prefix to filter the files to be uploaded. For KHP,
    FTCI files are prefixed with V2, and CSI files are prefixed with V1.

    Args:
        prefix (str, optional): Prefix of files to load. Defaults to None.
    """
    LOG.info("Loadings files with prefix {0} to S3".format(prefix))
    s3_bucket = S3_BUCKET
    keys = utils.get_s3_keys(s3_bucket)
    # get all files from output dir that is not in keys
    files = utils.search_path(config.FTP_OUTPUT_DIR, prefix=prefix)
    basenames = [os.path.basename(f) for f in files]
    unloaded_files = [os.path.join(config.FTP_OUTPUT_DIR, f)
                        for f in list(set(basenames) - set(keys))]

    if len(unloaded_files) > 0:
        utils.upload_to_s3(s3_bucket, unloaded_files)
    else:
        LOG.warning("No files to upload")

    utils.clean_dir(config.FTP_OUTPUT_DIR, prefix=prefix)

#TODO: Refactor report loading into a class!
def load_ftci_to_postgres():
    # get all files from output dir that have already been loaded
    db_conf = CONF['database']
    query = """
        SELECT report_name
        FROM loaded_reports
        WHERE report_type='FTCI' --AND load_dt > CURRENT_DATE - 2 -- can't add this part cuase files are still in S3
    """
    data = postgrez.execute(query=query, host=db_conf['host'],
                user=db_conf['user'], password=db_conf['pwd'],
                database=db_conf['db'])
    loaded_files = [record['report_name'] for record in data]
    # get files from S3 matching prefix
    files = utils.get_s3_keys(S3_BUCKET, prefix="V2")

    unloaded_files = list(set(files) - set(loaded_files))

    loaded_reports = []
    with postgrez.Load(
            host=db_conf['host'], user=db_conf['user'],
            password=db_conf['pwd'], database=db_conf['db']) as load:
        for key in unloaded_files:
            contents = utils.read_s3_file(S3_BUCKET, key)
            if contents == '':
                loaded_reports.append(key)
                continue
            parsed_contents = utils.parse_s3_contents(contents, '|',
                                                        remove_dupes=True)
            load.load_from_object(table_name='ftci',
                                    data=parsed_contents)
            loaded_reports.append(key)

        ## TODO: if one of these queries above fails, the loaded reports part below doesn't run...
        if len(loaded_reports) > 0:
            dt = datetime.now()
            load_data = [[dt, report_name, 'FTCI']
                            for report_name in loaded_reports]
            load.load_from_object(table_name='loaded_reports', data=load_data)


## TODO: make sure your read from s3 method is returning more than 1000
