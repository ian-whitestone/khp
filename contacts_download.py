import logging
from datetime import timedelta, datetime
import os

import postgrez
import utils
import config
from icescape import Icescape
from transforms import Transformer

FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
LOG = logging.getLogger(__name__)

logging.getLogger("botocore").setLevel(logging.WARNING)
logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.INFO)

CONF = config.CONFIG
db_conf = CONF['database']

def save_data(data, filename):
    """Save data from icescape API.

    Args:
        data (list or dict): data to save locally or in S3
        filename (str): filename to save data to
    """
    filepath = os.path.join(config.ICESCAPE_OUTPUT_DIR, filename)
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
            contact_data = ice.get_contacts(
                interaction_type, start_time=start_dt.strftime(tm_format),
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

def download_transcripts(contact_ids=None):
    """Download transcripts for a list of contact_ids.

    Args:
        contact_ids (list, optional): List of Contact IDs to retrieve recordings
            for. If None are provided (default), queries contacts that have not
            been parsed
    """
    db_conf = CONF['database']
    if contact_ids is None:
        query = """
            SELECT contact_id FROM contacts WHERE transcript_downloaded=FALSE
            """
        data = postgrez.execute(query=query, host=db_conf['host'],
                                user=db_conf['user'], password=db_conf['pwd'],
                                database=db_conf['db'])
        contact_ids = [record['contact_id'] for record in data]

    if not contact_ids:
        LOG.warning("No contact ids to parse. Exiting..")
        return

    ice = Icescape()
    transcripts = ice.get_recordings(contact_ids)
    if len(transcripts) != len(contact_ids):
        raise Exception("Transcripts not returned for all contact ids")
    for contact_id, transcript in zip(contact_ids, transcripts):
        filename = "{}_data.txt".format(contact_id)
        save_data(transcript, filename)

    update_query = """
        UPDATE contacts SET transcript_downloaded=TRUE WHERE contact_id IN ({})
        """.format(','.join([str(id) for id in contact_ids]))
    postgrez.execute(query=update_query, host=db_conf['host'],
                     user=db_conf['user'], password=db_conf['pwd'],
                     database=db_conf['db'])

def parse_contacts_file(filename):
    LOG.info("Parsing contact file %s", filename)
    db_conf = CONF['database']
    base_file = os.path.basename(filename)
    interaction_type = base_file.split('_')[0]

    contacts = utils.read_jason(filename)
    transforms_meta = config.TRANSFORMS["contacts"]
    optimus = Transformer(transforms_meta)

    parsed_contacts = []
    for contact in contacts:
        contact_data = optimus.run_transforms(contact)
        contact_data['interaction_type'] = interaction_type
        contact_data['transcript_downloaded'] = False
        contact_data['load_file'] = base_file
        parsed_contacts.append(contact_data)

    columns = list(parsed_contacts[0].keys())
    load_data = [[contact_data[key] for key in columns]
                 for contact_data in parsed_contacts]
    postgrez.load(table_name="contacts", data=load_data, columns=columns,
                  host=db_conf['host'], user=db_conf['user'],
                  password=db_conf['pwd'], database=db_conf['db'])

def parse_transcript(filename):
    LOG.info("Parsing transcript file %s", filename)
    db_conf = CONF['database']

    transcript = utils.read_jason(filename)
    transforms_meta = config.TRANSFORMS["transcript"]
    optimus = Transformer(transforms_meta)
    output = optimus.run_transforms(transcript)
    messages = output['messages']

    columns = list(messages[0].keys())
    load_data = [[message[key] for key in columns]
                 for message in messages]

    postgrez.load(table_name="transcripts", data=load_data, columns=columns,
                  host=db_conf['host'], user=db_conf['user'],
                  password=db_conf['pwd'], database=db_conf['db'])
    return


def get_contacts_to_load():
    """Grab the filenames of all contact files that have not been loaded to
    Postgres.

    Returns:
        list: List of contact files to load
    """
    contacts_reg = r"\w*_\d{4}-\d{1,2}-\d{1,2}_\w*"
    query = "SELECT load_file FROM contacts GROUP BY 1"
    data = postgrez.execute(query, host=db_conf['host'], user=db_conf['user'],
                            password=db_conf['pwd'], database=db_conf['db'])
    loaded_files = [record['load_file'] for record in data]
    files = utils.search_path(config.ICESCAPE_OUTPUT_DIR, [contacts_reg])
    filenames = [os.path.basename(file) for file in files]

    return list(set(filenames) - set(loaded_files))

def get_transcripts_to_load():
    """Grab the filenames of all transcript files that have not been loaded to
    Postgres

    Returns:
        list: List of trancsript files to load
    """
    query = "SELECT contact_id FROM transcripts GROUP BY 1"
    data = postgrez.execute(query, host=db_conf['host'], user=db_conf['user'],
                            password=db_conf['pwd'], database=db_conf['db'])
    data = [record['contact_id'] for record in data]
    return

def main(start_date=None, end_date=None):
    if start_date is None and end_date is None:
        yesterday = datetime.today() - timedelta(1)
        start_date = yesterday.strftime('%Y-%m-%d')
        end_date = start_date

    if start_date is None or end_date is None:
        LOG.warning("Provide both start_date and end_date. Exiting..")
        return

    ## DOWNLOAD CONTACTS ##
    download_contacts("IM", start_date, end_date)

    ## CONTACTS LOADING ##
    contacts_to_load = get_contacts_to_load()
    for contact_file in contacts_to_load:
        full_path = os.path.join(config.ICESCAPE_OUTPUT_DIR, contact_file)
        parse_contacts_file(full_path)

    ## DOWNLOAD TRANSCRIPTS ##
    download_transcripts()
    ## TRANSCRIPTS LOADING ##
    transcripts_to_load = get_transcripts_to_load()
    for transcript_file in transcripts_to_load:
        full_path = os.path.join(config.ICESCAPE_OUTPUT_DIR, transcript_file)
        parse_transcript(full_path)

if __name__ == '__main__':
    main()

