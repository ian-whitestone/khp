"""
Module to handle connecting to the KHP FTP server.
Enforces using TLS/SSL implicit encryption, which is required by their server.

Modified from:
https://stackoverflow.com/questions/12164470/python-ftp-implicit-tls-connection-issue
"""

import logging
import ftplib_mod as ftplib
import socket
import ssl

log = logging.getLogger(__name__)

class tyFTP(ftplib.FTP_TLS):

    def __init__(self, host='', user='', passwd='', acct='', keyfile=None,
                    certfile=None, timeout=60):

        ftplib.FTP_TLS.__init__(self, host=host, user=user, passwd=passwd,
                                    acct=acct, keyfile=keyfile,
                                    certfile=certfile, timeout=timeout)

    def connect(self, host='', port=0, timeout=-999):
        """Connect to FTP host.

        Args:
            host (str): hostname to connect to
            port (int): port to connect to

        Raises:
            Exception: If the connection fails.
        """
        if host != '':
            self.host = host
        if port > 0:
            self.port = port
        if timeout != -999:
            self.timeout = timeout
        try:
            self.sock = socket.create_connection((self.host, self.port),
                                                    self.timeout)
            self.af = self.sock.family
            self.sock = ssl.wrap_socket(self.sock,
                                        self.keyfile,
                                        self.certfile,
                                        ssl_version=ssl.PROTOCOL_TLSv1)
            self.file = self.sock.makefile('rb')
            self.welcome = self.getresp()
        except Exception as e:
            log.error("Unable to connect due to error: %s" % e, exc_info=True)
        return self.welcome


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, exc_tb):
        """Close the FTP connection.
        This code is automatically executed after the with statement is
        completed or if any error arises during the process.
        Ref: https://stackoverflow.com/questions/1984325/explaining-pythons-enter-and-exit
        """
        log.debug("Attempting to close connection ...")
        self.quit()
        log.debug("Connection closed")
