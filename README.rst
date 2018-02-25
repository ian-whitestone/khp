=======================
KHP
=======================


|build| |coverage| |license|

.. code-block:: bash

        __   _     ___          __         __               __
       / /__(_)___/ ( )_____   / /_  ___  / /___     ____  / /_  ____  ____  ___
      / //_/ / __  /|// ___/  / __ \/ _ \/ / __ \   / __ \/ __ \/ __ \/ __ \/ _ \
     / ,< / / /_/ /  (__  )  / / / /  __/ / /_/ /  / /_/ / / / / /_/ / / / /  __/
    /_/|_/_/\__,_/  /____/  /_/ /_/\___/_/ .___/  / .___/_/ /_/\____/_/ /_/\___/
                                        /_/      /_/


Data infrastructure for the Kids Help Phone.

FTP Servers
------------

.. code-block:: python

    from khp import ftp
    from khp import config

    ## CSI Files
    ## Run every 10 minutes
    download('CSI_files', config.FTP_OUTPUT_DIR)
    load_to_s3("V1")

    ## FTCI Files
    ## Run twice per day
    download('FTCI_files/Archive', config.FTP_OUTPUT_DIR)
    load_to_s3("V2")
    load_ftci_to_postgres()


Icescape
--------

.. code-block:: python

    from khp import contacts

    contacts.main()


.. |build| image:: https://img.shields.io/circleci/project/github/ian-whitestone/postgrez.svg
    :target: https://circleci.com/gh/ian-whitestone/postgrez
.. |coverage| image:: https://coveralls.io/repos/github/ian-whitestone/postgrez/badge.svg
    :target: https://coveralls.io/github/ian-whitestone/postgrez
.. |license| image:: https://img.shields.io/badge/License-MIT-yellow.svg
    :target: https://github.com/ian-whitestone/khp/blob/master/LICENSE