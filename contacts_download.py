import config
import os
import utils
from icescape import Icescape
import logging
from datetime import timedelta, datetime

FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
log = logging.getLogger(__name__)

logging.getLogger("botocore").setLevel(logging.WARNING)
logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.INFO)

def save_data(data, filename, s3=False):
    """Save data from icescape API.

    Args:
        data (list or dict): data to save locally or in S3
        filename (str): filename to save data to
        s3 (bool, optional): write data to s3. Defaults to False
    """

    filepath = os.path.join(config.ICESCAPE_OUTPUT_DIR, filename)
    if s3:
        #TODO: implement
        pass
    else:
        utils.write_jason(data, filepath)

def download_contacts(interaction_type, start_date=None, end_date=None):
    ice = Icescape()
    if start_date and end_date:
        date_range = utils.generate_date_range(start_date, end_date)
        for start_dt in date_range:
            end_dt = start_dt + timedelta(days=1) - timedelta(milliseconds=1)
            contact_data = ice.get_contacts(interaction_type,
                start_time=start_dt, end_time=end_dt)
            filename = "{}_contacts.txt".format(start_dt.strftime("%Y-%m-%d"))
            save_data(contact_data, filename)
    else:
        contact_data = ice.get_contacts(interaction_type)
        start_dt = datetime.now() - timedelta(1)
        filename = "{}_contacts.txt".format(start_dt.strftime("%Y-%m-%d"))
        save_data(contact_data, filename)

# recording_data = ice.get_recordings([197132, 197132])
# print (len(data))

download_contacts("IM")
