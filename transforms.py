import sys
from functools import reduce

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
    output["agent_id"] = handlers[0]
    if len(handlers) == 1:
        output["secondary_agents"] = None
    else:
        output["secondary_agents"] = ",".join(handlers[1:])
    return output

def parse_message():
    """
    """
    pass


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
            field_name = list(field_dict.keys())[0]
            items = field_dict[field_name]
            transforms.append({'field_name': field_name, 'items': items})
        return transforms

    def run_transforms(self, data):
        """Run the transforms on a supplied dictionary of data.

        Args:
            data (dict):

        Returns:
            transformed (dict): data that has been parsed, re-mapped and
                transformed according to the self.transforms instructions
        """
        transformed = {}
        for transform in self.transforms:
            value = self._get_value(transform['field_name'], data)
            items = transform['items']
            if "transform" in items.keys():
                value = getattr(sys.modules[__name__], items["transform"])(
                        value)

            if type(value) == dict:
                transformed = {**transformed, **value}
            else:
                transformed[items["name"]] = value

        return transformed
