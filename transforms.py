import re
import sys
from functools import reduce
from bs4 import BeautifulSoup

def parse_handlers(handlers):
    """Parse the handlers associated with a contact. Split out primary handler
    and secondary handlers, assuming primary handler as the first handler in
    the list of handlers.

    Args:
        handlers (list): List of handlers

    Returns:
        output (dict): Dictionary containing primary and secondary handlers
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

def parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    return soup.get_text()


def parse_message(message_text, is_html):
    if is_html:
        parsed_text = parse_html(message_text)
    else:
        parsed_text = message_text

    # strip newlines
    parsed_text = ' '.join(parsed_text.split())
    return parsed_text

def parse_messages(messages):
    """
    """
    name_map = {'Sender': 'sender', 'Timestamp': 'dt',
                'MessageType': 'message_type', 'Message': 'message',
                'ContactId': 'contact_id', 'DisplayName': 'display_name'}
    output_messages = []
    for message in messages:
        transformed = {name_map[k]:v for k,v in message.items()
                        if k in name_map.keys()}
        transformed['message'] = parse_message(transformed['message'],
                                               message['IsHtml'])
        output_messages.append(transformed)
    return output_messages


class Transformer():
    """
    """

    def __init__(self, transforms_meta):
        """
        """
        self.transforms_meta = transforms_meta
        self.transforms = self._parse_transforms(transforms_meta)


    def _get_value(self, field_name, data):
        """
        """
        keys = field_name.split('|')
        return reduce(lambda c, k: c.get(k, {}), keys, data)


    def _parse_transforms(self, transforms_meta):
        """
        """
        transforms = []
        for field_dict in transforms_meta:
            field_name = next(iter(field_dict))
            # transforms.yml has special fields reserved by '__XXX__'
            if re.search(r"__.*__", field_name):
                continue
            items = field_dict[field_name]
            transforms.append({'field_name': field_name, 'items': items})
        return transforms

    def run_transforms(self, data):
        """Run the transforms on a supplied dictionary of data.

        Args:
            data (dict):

        Returns:
            transformed (list or dict): data that has been parsed, re-mapped and
                transformed according to the self.transforms instructions
        """
        transformed = {}
        for transform in self.transforms:
            value = self._get_value(transform['field_name'], data)
            items = transform['items']
            if "transform" in items.keys():
                value = getattr(sys.modules[__name__], items["transform"])(
                        value)

            # Some transforms may return two fields, i.e. {'a': 5, 'b': 10}
            if type(value) == dict:
                transformed = {**transformed, **value}
            else:
                transformed[items["name"]] = value

        return transformed

#TODO: add logging
