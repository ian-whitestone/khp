"""Module containing a set of transformations that are run are the JSON
responses from the API, and the transcript dataframes.
"""
import builtins
import logging
import operator
import re
import sys
from functools import reduce
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

LOG = logging.getLogger(__name__)

def convo_start_indicator(dataframe):
    """Create an indicator for each message to signal whether it's the start of
    the conversation. Starting messages are detected using a regex, since the
    starting messages are system generated (hence filtering on message_type=1).

    Args:
        dataframe (pandas.DataFrame): Input dataframe
        parameters (dict): Parameters associated with the transform

    Returns:
        pandas.Series: Conversation start indicator
    """
    joined_reg = r"(?:(?:joined\sthe\s)|(?:sest\sjoint\s.\sla\s))conversation\."
    mtype_check = dataframe['message_type'] == 1
    reg_check = dataframe['message'].str.contains(joined_reg)
    convo_start_ind = pd.Series(0, index=dataframe.index)
    convo_start_ind.loc[mtype_check & reg_check] = 1
    return convo_start_ind

def convo_indicator(dataframe):
    """Create an indicator for each message to signal whether it's part of the
    conversation. A message is deemed part of the conversation if it appears
    after the convo_start_ind messages and is message type 3 or 4.

    Args:
        dataframe (pandas.DataFrame): Input dataframe
        parameters (dict): Parameters associated with the transform

    Returns:
        pandas.Series: Conversation indicator
    """
    mtype_check = dataframe['message_type'].isin([3, 4])
    start_index = max(dataframe[dataframe['convo_start_ind'] == 1].index)
    index_check = dataframe.index > start_index
    convo_ind = pd.Series(0, index=dataframe.index)
    convo_ind.loc[mtype_check & index_check] = 1
    return convo_ind

def calc_wait_time(dataframe):
    """Calculate the wait time for a contact. Wait time is calculated as
    time elasped between the start of the transcript and the first message
    with convo_ind == 1.

    Args:
        dataframe (pandas.DataFrame): Input dataframe
        parameters (dict): Parameters associated with the transform

    Returns:
        float: Wait time for the contact, in minutes
    """
    start_queue_time = dataframe['dt'].min()
    end_queue_time = dataframe[dataframe['convo_ind'] == 1]['dt'].min()
    return convert_timedelta((end_queue_time-start_queue_time), 'm')

def calc_handle_time(dataframe):
    """Calculate the handle time for a contact. Handle time is calculated as
    time elasped between all messages with convo_ind == 1.

    Args:
        dataframe (pandas.DataFrame): Input dataframe
        parameters (dict): Parameters associated with the transform

    Returns:
        float: Handle time for the contact, in minutes
    """
    start_convo_time = dataframe[dataframe['convo_ind'] == 1]['dt'].min()
    end_convo_time = dataframe[dataframe['convo_ind'] == 1]['dt'].max()
    return convert_timedelta((end_convo_time-start_convo_time), 'm')

def calc_response_time(dataframe):
    """Calculate the response time for each message. Defined as time elapsed
    between message and previous message.

    Args:
        dataframe (pandas.DataFrame): Input dataframe
        parameters (dict): Parameters associated with the transform

    Returns:
        pandas.Series: Response time for the message
    """
    dataframe['prev_message_time'] = dataframe['dt'].shift(1)
    null_check = pd.isnull(dataframe['prev_message_time'])
    dataframe.loc[null_check, 'prev_message_time'] = dataframe['dt']
    return dataframe['dt'] - dataframe['prev_message_time']

def calc_message_sequence(dataframe):
    """Calculate the message sequence for each message, defined as:
    'prev_message_type' - 'message_type', used to indicate whether a message
    was from counsellor to counsellor, counselee to counsellor, system to
    counsellor etc.

    Args:
        dataframe (pandas.DataFrame): Input dataframe
        parameters (dict): Parameters associated with the transform

    Returns:
        pandas.Series: Message sequence
    """
    dataframe['prev_message_type'] = dataframe['message_type'].shift(1)
    null_check = pd.isnull(dataframe['prev_message_type'])
    dataframe.loc[null_check, 'prev_message_type'] = dataframe['message_type']
    message_seq = dataframe['prev_message_type'].astype(int).astype(str) + '-' \
        + dataframe['message_type'].astype(str)
    return message_seq

def str_length(dataframe, parameters):
    """Calculate the length of a string

    Args:
        dataframe (pandas.DataFrame): Input dataframe
        parameters (dict): Parameters associated with the transform

    Returns:
        pandas.Series: Number of characters for each row of a column
    """
    return dataframe[parameters['column_name']].str.len()

def word_count(dataframe, parameters):
    """Count the number of words in a string

    Args:
        dataframe (pandas.DataFrame): Input dataframe
        parameters (dict): Parameters associated with the transform

    Returns:
        pandas.Series: Word counts for each row of a column
    """
    str_series = dataframe[parameters['column_name']].fillna('')
    return str_series.str.split().apply(len)

def parse_handlers(handlers):
    """Parse the handlers associated with a contact. Split out primary handler
    and secondary handlers, assuming primary handler as the first handler in
    the list of handlers.

    Args:
        handlers (list): List of handlers

    Returns:
        dict: Dictionary containing primary and secondary handlers
    """
    output = {}
    if not handlers: # no handlers on the call
        output['agent_id'] = None
        output['secondary_agents'] = None
    elif len(handlers) == 1: # 1 handler
        output["agent_id"] = handlers[0]
        output["secondary_agents"] = None
    else: # more than 2 handlers
        output["agent_id"] = handlers[0]
        output["secondary_agents"] = ",".join(handlers[1:])

    return output

def filter_df(dataframe, filters):
    """Filter a dataframe

    Args:
        dataframe (pandas.DataFrame): Input dataframe
        filters (list): list of filters (dicts) to apply

    Returns:
        pandas.DataFrame: Filtered dataframe
    """
    for fltr_dict in filters:
        fltr_fn = getattr(operator, fltr_dict['operator'])
        fltr_value = fltr_dict['value']
        fltr_value = getattr(builtins, fltr_dict['value_type'])(fltr_value)
        fltr_check = fltr_fn(dataframe[fltr_dict['column']], fltr_value)
        fltr_df = dataframe[fltr_check]
    return fltr_df

def row_count(dataframe, parameters):
    """Count the number of rows in a dataframe, optionally applying filters
    specified in parameters.

    Args:
        dataframe (pandas.DataFrame): Input dataframe
        parameters (dict): Parameters associated with the transform

    Returns:
        int: Number of rows
    """
    if 'filters' in parameters.keys():
        fltr_df = filter_df(dataframe, parameters['filters'])
    else:
        fltr_df = dataframe

    return fltr_df.shape[0]

def column_operator(dataframe, parameters):
    """Apply a numpy operator on a column in a dataframe, optionally applying
    filters specified in parameters.

    If multiple aggregators are supplied, a dictionary will be returned instead
    of the float result. For example, if the following parameters are provided:

    parameters = {
        'output': khp_response_time,
        'aggregator': [mean, max]
    }

    Function will return:

    {mean_khp_response_time: 1.2325, max_khp_response_time: 55.212}

    Args:
        dataframe (pandas.DataFrame): Input dataframe
        parameters (dict): Parameters associated with the transform

    Returns:
        dict or float: If multiple aggregators are supplied, returns a dict
            with the result of each aggregator. Otherwise, returns the float
            result of the aggregator operation.
    """
    fltr_df = dataframe
    if 'filters' in parameters.keys():
        fltr_df = filter_df(dataframe, parameters['filters'])

    post_operator = None
    if 'post_operator' in parameters.keys():
        post = parameters['post_operator']
        post_operator = getattr(sys.modules[__name__], post['name'])
        post_args = post['args']

    if isinstance(parameters['aggregator'], list):
        result = {}
        for agg_name in parameters['aggregator']:
            agg = getattr(np, agg_name)
            output_name = '{}_{}'.format(agg_name, parameters['output'])
            series = getattr(dataframe, parameters['column'])
            if post_operator:
                result[output_name] = post_operator(agg(series), post_args)
            else:
                result[output_name] = agg(series)
    else:
        agg_name = parameters['aggregator']
        agg = getattr(np, agg_name)
        series = getattr(dataframe, parameters['column'])
        if post_operator:
            result = post_operator(agg(series), post_args)
        else:
            result = agg(series)
    return result

def convert_timedelta(value, unit):
    """Convert a timedelta64 object to a float

    Args:
        value (numpy.timedelta64[ns]): Timedelta value to convert
        unit (TYPE): Datetime unit code, see link for a list of acceptable codes
            https://docs.scipy.org/doc/numpy-dev/reference/arrays.datetime.html

    Returns:
        float: Converted timedelta value
    """
    return value / np.timedelta64(1, unit)

def parse_html(html):
    """Utilize the beautiful soup html parser to return the text from html

    Args:
        html (str): String of html

    Returns:
        str: extracted text
    """
    soup = BeautifulSoup(html, 'html.parser')
    return soup.get_text()


def clean_text(text):
    """Function to sanitize the trnascript messages. Replaces all whitespace
    with single spaces (since newlines break things when uploading to the DB).
    Get rid of everything that isn't a number, letter, or in a list of
    characters to keep.

    Args:
        text (str): Text string to clean

    Returns:
        str: Cleaned text str
    """
    ## replace newlines with spaces
    text = ' '.join(text.split())
    keep = [' ', '!', '?', '[', ']', '(', ')', '.', '$', '#', '*', ',', ':',
            ';']
    # get rid of everything that isn't a number, letter, or in keep
    text = ''.join([char for char in text if char.isalnum() or char in keep])
    return text

def parse_message(message_text, is_html):
    """Return the text from a (potentially) html message string

    Args:
        message_text (str): Description
        is_html (bool): Boolean indicator whether the text is html, provided
            upstream from the API response.

    Returns:
        str: Parsed message text
    """
    if is_html:
        parsed_text = parse_html(message_text)
    else:
        parsed_text = message_text

    parsed_text = clean_text(parsed_text)
    return parsed_text

def parse_messages(messages):
    """Transformation function to parse a list of messages

    Args:
        messages (list): List of message dicts

    Returns:
        list: List of transformed message dicts
    """
    name_map = {'Sender': 'sender', 'Timestamp': 'dt',
                'MessageType': 'message_type', 'Message': 'message',
                'ContactId': 'contact_id', 'DisplayName': 'display_name'}
    output_messages = []
    for message in messages:
        # remap message dict keys with the name_map specified above
        transformed = {name_map[k]:v for k, v in message.items()
                       if k in name_map.keys()}
        transformed['message'] = parse_message(transformed['message'],
                                               message['IsHtml'])
        output_messages.append(transformed)
    return output_messages


class Transformer():
    """A class that ingests a dictionary of transforms, and runs those
    transforms on a supplied dictionary or dataframe.

    Attributes:
        transforms (list): List of the transformation dictionaries.
    """

    def __init__(self, transforms_meta):
        """Load and parse the meta transformations data.

        Args:
            transforms_meta (list): List of the raw transformation dictionaries.
        """
        self.transforms = self.parse_transforms(transforms_meta)

    @staticmethod
    def get_value(key, data):
        """Grab the value associated with a key in a dictionary. Supports the
        nested key definitions in transforms.yml. For example, a key of
        'KEY1|KEY2|KEY3' will return 5 from the following data:

        data = {
            'KEY1': {
                'KEY2': {'KEY3': 5, ...},
                ...
            },
            ...
        }

        Args:
            key (str): Dictionary key of the value to return
            data (dict): Dictionary of data to return value from

        Returns:
            any type: Returns the value associated with the specified key(s)
        """
        keys = key.split('|')
        return reduce(lambda c, k: c.get(k, {}), keys, data)

    @staticmethod
    def parse_transforms(transforms_meta):
        """Parse the list of raw transformations. Generally, each transformation
        (i.e. each element of transforms_meta) will be in the following format:

        {
            'field_name':
                {
                    'key1': 'value1',
                    'key2': 'value2',
                    ...
                }
        }

        Args:
            transforms_meta (list): List of the raw transformation dictionaries.

        Returns:
            list: List of the transformation dictionaries.
        """
        transforms = []
        for field_dict in transforms_meta:
            field_name = next(iter(field_dict))
            # transforms.yml has special fields reserved by '__XXX__'
            # currently not using this functionality
            if re.search(r"__.*__", field_name):
                continue
            items = field_dict[field_name]
            transforms.append({'name': field_name, 'items': items})
        return transforms

    @staticmethod
    def get_input_cols(transform_dict):
        """Return the input columns associated with a transformation

        Args:
            transform_dict (dict): Transform dict parsed from transforms.yml

        Returns:
            list: list of input columns
        """
        input_cols = transform_dict['input']
        if not isinstance(input_cols, list):
            input_cols = [input_cols]
        return input_cols

    def run_df_transforms(self, dataframe):
        """Run the transforms on a supplied dataframe.

        Args:
            dataframe (pandas.Dataframe): Input dataframe to run transformation
                on.

        Returns:
            pandas.Dataframe: Dataframe with updated and/or new columns
        """
        for tform in self.transforms:
            transform_name = tform['name']
            # input_cols = self.get_input_cols(tform['items'])
            parameters = tform['items']
            output_name = parameters['output']
            transform = getattr(sys.modules[__name__], transform_name)
            LOG.info('Running transform: %s on input dataframe with params %s',
                     transform_name, parameters)
            if 'parameters' in transform.__code__.co_varnames:
                dataframe[output_name] = transform(dataframe, parameters)
            else:
                dataframe[output_name] = transform(dataframe)

        return dataframe

    def run_meta_df_transforms(self, dataframe):
        """Run transforms on a supplied dataframe.

        Args:
            dataframe (pandas.Dataframe): Input dataframe to run transformation
                on.

        Returns:
            dict: Output dictionary from the input dataframe
        """
        metadata = {}
        for tform in self.transforms:
            transform_name = tform['name']
            parameters = tform['items']
            output_name = parameters['output']
            transform = getattr(sys.modules[__name__], transform_name)
            LOG.info('Running transform: %s on input dataframe with params %s',
                     transform_name, parameters)
            if 'parameters' in transform.__code__.co_varnames:
                output = transform(dataframe, parameters)
            else:
                output = transform(dataframe)
            if isinstance(output, dict):
                metadata = {**metadata, **output}
            else:
                metadata[output_name] = output
        return metadata

    def run_transforms(self, data):
        """Run the transforms on a supplied dictionary of data.

        Args:
            data (dict): dictionary of data to run transformation on

        Returns:
            (list or dict): data that has been parsed, re-mapped and
                transformed according to the self.transforms instructions
        """
        transformed = {}
        for transform in self.transforms:
            value = self.get_value(transform['name'], data)
            items = transform['items']
            if "transform" in items.keys():
                func_name = items["transform"]
                LOG.info('Running transform: %s on data', func_name)
                tform_func = getattr(sys.modules[__name__], func_name)
                value = tform_func(value)

            # Some transforms may return two fields, i.e. {'a': 5, 'b': 10}
            if isinstance(value, dict):
                transformed = {**transformed, **value}
            else:
                transformed[items["name"]] = value

        return transformed
