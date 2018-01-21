import logging
FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
log = logging.getLogger(__name__)

import boto3
import os
import config
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


download('CSI_files', config.OUTPUT_DIR)
download('FTCI_files/Archive', config.OUTPUT_DIR)
