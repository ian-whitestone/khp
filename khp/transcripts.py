"""Process all the transcript json files to extract survey details
and load them to the database
"""

import logging
from datetime import timedelta, datetime
import os
import json

import dask.bag as db
from glom import glom, Coalesce, Call, T
import postgrez

from khp import transforms
from khp import config

LOGGER = logging.getLogger(__name__)
CONF = config.CONFIG
DB_CONF = CONF['database']

# initialize logging to file and stdout
config.init_logging()

def survey_response(message):
    distress_score = None
    for message_text in message['messages']:
        if 'User profile:' in message_text \
            or 'Pre survey response' in message_text \
            or 'Sondage avant le clavardage' in message_text:
            text = message_text.split('How upset are you right now?:')
            if len(text) > 1:
                distress_score = text[1].strip()
                break

            text = message_text.split('en ce moment?:')
            if len(text) > 1:
                distress_score = text[1].strip()
                break
    message['score'] = distress_score
    return message

def parse_message_handler(message):
    return transforms.parse_message(message['Message'], message['IsHtml'])

def parse_distress_score(x):
    if x is not None:
        return int(float(x))

base_spec = {
    'contact_id': 'Value.ContactID',
    'messages': (
        'Value.IMMessages.Value', [lambda x: parse_message_handler(x)]
        )
}

final_spec = {
    'contact_id': 'contact_id',
    'score': ('score', lambda x: parse_distress_score(x))
}

path = os.path.join(config.ICESCAPE_OUTPUT_DIR, '*_data.txt')
bag = db.read_text(path).map(json.loads)
bag = bag.map(glom, base_spec)
bag = bag.map(survey_response)
bag = bag.map(glom, final_spec)
results = bag.compute()


# scores = [int(float(r['score'])) for r in res if r['score'] is not None]
# print (len(scores))
# print (len(res))


columns = list(results[0].keys())
load_data = [[result[key] for key in columns] for result in results]

postgrez.load(table_name="distress_scores", data=load_data, columns=columns,
              host=DB_CONF['host'], user=DB_CONF['user'],
              password=DB_CONF['pwd'], database=DB_CONF['db'])
