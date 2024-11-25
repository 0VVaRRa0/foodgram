from hashids import Hashids

from .constants import SHORT_LINK_MIN_LENGTH


def generate_short_link(obj_id):
    hashids = Hashids(min_length=SHORT_LINK_MIN_LENGTH)
    return hashids.encode(obj_id)
