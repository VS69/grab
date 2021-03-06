import urllib
from urlparse import urlsplit, urlunsplit
import re

from ..base import UploadFile, UploadContent
from ..error import GrabMisuseError
from .encoding import smart_str, smart_unicode

RE_NON_ASCII = re.compile(r'[^-.a-zA-Z0-9]')

def urlencode(items, charset='utf-8'):
    """
    Convert sequence of items into bytestring which could be submitted
    in POST or GET request.

    It differs from ``urllib.urlencode`` in that it can process unicode
    and some special values.

    ``items`` could dict or tuple or list.
    """

    if isinstance(items, dict):
        items = items.items()
    return urllib.urlencode(normalize_http_values(items, charset=charset))


def encode_cookies(items, join=True, charset='utf-8'):
    """
    Serialize dict or sequence of two-element items into string suitable
    for sending in Cookie http header.
    """

    def encode(val):
        """
        URL-encode special characters in the text.

        In cookie value only ",", " ", "\t" and ";" should be encoded
        """

        return val.replace(' ', '%20').replace('\t', '%09')\
                  .replace(';', '%3B').replace(',', '%2C')

    if isinstance(items, dict):
        items = items.items()
    items = normalize_http_values(items, charset=charset)
    tokens = []
    for key, value in items:
        tokens.append('%s=%s' % (encode(key), encode(value)))
    if join:
        return '; '.join(tokens)
    else:
        return tokens


def normalize_http_values(items, charset='utf-8'):
    """
    Accept sequence of (key, value) paris or dict and convert each
    value into bytestring.

    Unicode is converted into bytestring using charset of previous response
    (or utf-8, if no requests were performed)

    None is converted into empty string. 

    Instances of ``UploadContent`` or ``UploadFile`` is converted
    into special pycurl objects.
    """

    if isinstance(items, dict):
        items = items.items()

    def process(item):
        key, value = item

        # normalize value
        if isinstance(value, (UploadContent, UploadFile)):
            value = value.field_tuple()
        elif isinstance(value, unicode):
            value = normalize_unicode(value, charset=charset)
        elif value is None:
            value = ''

        # normalize key
        if isinstance(key, unicode):
            key = normalize_unicode(key, charset=charset)

        return key, value

    items =  map(process, items)
    #items = sorted(items, key=lambda x: x[0])
    return items


def normalize_unicode(value, charset='utf-8'):
    """
    Convert unicode into byte-string using detected charset (default or from
    previous response)

    By default, charset from previous response is used to encode unicode into
    byte-string but you can enforce charset with ``charset`` option
    """

    if not isinstance(value, unicode):
        raise GrabMisuseError('normalize_unicode function accepts only unicode values')
    return value.encode(charset, 'ignore')


def quote(data):
    return urllib.quote_plus(smart_str(data))


def normalize_url(url):
    parts = list(urlsplit(url))
    if RE_NON_ASCII.search(parts[1]):
        parts[1] = smart_unicode(parts[1]).encode('idna')
        url = urlunsplit(parts)
        return url
    else:
        return url
