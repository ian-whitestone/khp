import config
import os
import utils
from icescape import Icescape
from transforms import Transformer
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
    """Download contacts for a given interaction type and time period, and save
    the data.

    Args:
        interaction_type (str): Type of contact (i.e. IM, Voice, Email)
        start_date (str, optional): Start time, `YYYY-mm-dd`. Defaults to
            beginning of yesterday.
        start_date (str, optional): End time, `YYYY-mm-dd`. Defaults to
            end of yesterday.
    """
    ice = Icescape()
    dt_format = "%Y-%m-%d"
    tm_format = '%Y-%m-%dT%H:%M:%S.%f'
    if start_date and end_date:
        date_range = utils.generate_date_range(start_date, end_date)
        for start_dt in date_range:
            end_dt = start_dt + timedelta(days=1) - timedelta(milliseconds=1)
            contact_data = ice.get_contacts(interaction_type,
                start_time=start_dt.strftime(tm_format),
                end_time=end_dt.strftime(tm_format))
            filename = "{}_{}_contacts.txt".format(interaction_type,
                            start_dt.strftime(dt_format))
            save_data(contact_data, filename)
    else:
        contact_data = ice.get_contacts(interaction_type)
        start_dt = datetime.now() - timedelta(1)
        filename = "{}_{}_contacts.txt".format(interaction_type,
                        start_dt.strftime("%Y-%m-%d"))
        save_data(contact_data, filename)

def download_transcripts(contact_ids):
    """Download transcripts for a list of contact_ids.

    Args:
        contact_ids (list): List of Contact IDs to retrieve recordings for
    """
    #TODO: get list of contact ids to retrieve from database...
    ice = Icescape()
    transcripts = ice.get_recordings(contact_ids)
    if len(transcripts) != len(contact_ids):
        raise Exception("Transcripts not returned for all contact ids")
    for contact_id, transcript in zip(contact_ids, transcripts):
        filename = "{}_data.txt".format(contact_id)
        save_data(transcript, filename)


def parse_contacts_file(filename):
    contacts = utils.read_jason(filename)
    transforms_meta = config.TRANSFORMS["contacts"]
    optimus = Transformer(transforms_meta)

    for contact in contacts:
        contact_data = optimus.run_transforms(contact)
        print (contact_data)
        break


download_contacts("IM", "2017-09-01", "2018-02-10")
# download_transcripts([197621])

# parse_contacts_file("output/icescape/2018-02-10_contacts.txt")
# transcript = utils.read_jason("output/icescape/197621_data.txt")


# print (transformed)

## note on contacts you will have to loop through each contact and run_transform on dict
