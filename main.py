import logging
FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
log = logging.getLogger(__name__)
logging.getLogger("botocore").setLevel(logging.WARNING)
logging.getLogger("boto3").setLevel(logging.WARNING)


import os
import config
import utils
from ImplicitlyTLS import tyFTP


CONF = config.CONFIG

def download(folder, output_dir):
    """Download files from a folder within the KHP FTP server.

    Args:
        folder (str): folder to download files from
    """
    log.info('Downloading files from FTP folder %s' % folder)
    with tyFTP() as ftp:
        log.debug("Connecting to host %s" % CONF['host'])
        ftp.connect(host=CONF['host'].encode("ascii"), port=CONF['port'])
        log.debug("Logging into host %s" % CONF['host'])
        ftp.login(user=CONF['user'], passwd=CONF['password'])
        log.debug("Switching to secure data connection")
        ftp.prot_p()
        ftp.cwd(folder)
        files = []
        ftp.retrlines("LIST", files.append)
        log.debug('{0} files found in folder {1}'.format(len(files), folder))
        for ftp_file in files:
            words = ftp_file.split(None, 8)
            filename = words[-1].lstrip()
            log.debug("Writing file %s" % filename)
            output_file = os.path.join(config.OUTPUT_DIR, filename)
            with open(output_file, "wb") as f:
                ftp.retrbinary("RETR " + filename, f.write, 8*1024)

def load_to_s3(prefix=None):
    """Load the downloaded files to S3, that have not already been uploaded.

    Args:
        prefix (str, optional): Prefix of files to load. Defaults to None.
    """
    log.info("Loadings files with prefix {0} to S3".format(prefix))
    s3_bucket = CONF['s3_bucket']
    keys = utils.get_s3_keys(s3_bucket)
    # get all files from output dir that is not in keys
    files = utils.search_path(config.OUTPUT_DIR, prefix=prefix)
    basenames = [os.path.basename(f) for f in files]
    unloaded_files = [os.path.join(config.OUTPUT_DIR, f)
                        for f in list(set(basenames) - set(keys))]

    if len(unloaded_files) > 0:
        utils.upload_to_s3(s3_bucket, unloaded_files)
    else:
        log.warning("No files to upload")

    utils.clean_dir(config.OUTPUT_DIR, prefix=prefix)

# download('CSI_files', config.OUTPUT_DIR)
download('FTCI_files/Archive', config.OUTPUT_DIR)
load_to_s3("V2")
