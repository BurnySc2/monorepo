# Simpler dict manipulation https://pypi.org/project/dpath/
from dpath.util import get, merge, new
from loguru import logger


def modify_dictionary():
    my_dict = {}

    # Create new path in dict
    new(my_dict, ['this', 'is', 'my', 'path'], value=5)

    # Merge dict to "my_dict"
    to_merge = {'this': {'is': {'another': {'dict': 6}}}}
    merge(my_dict, to_merge)

    # Get a value, if it doesn't exist: return default
    value = my_dict['this']['is']['my']['path']
    assert value == 5

    value_again = get(my_dict, ['this', 'is', 'my', 'path'])
    assert value_again == 5

    value = get(my_dict, ['this', 'path', 'doesnt', 'exist'], default=4)
    assert value == 4

    value = get(my_dict, ['this', 'is', 'another', 'dict'], default=7)
    assert value == 6

    logger.info(my_dict)
