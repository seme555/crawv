from contextlib import suppress

import re
import parsel
from w3lib.encoding import (html_body_declared_encoding, html_to_unicode,
                            http_content_type_encoding, resolve_encoding)
from w3lib.html import strip_html5_whitespace
from parsel import Selector

from crawv.http import Request
from crawv.http.response import Response
from crawv.utils.tools import to_unicode, memoizemethod_noargs, call_helper


class TextResponse(Response):

    _DEFAULT_ENCODING = 'ascii'

    def __init__(self, *args, **kwargs):
        self._encoding = kwargs.pop('encoding', None) or "utf-8"
        self._cached_benc = None
        self._cached_ubody = None
        self._cached_selector = None
        self.cookies = self._set_cookies(kwargs.pop("cookies", None))
        super(TextResponse, self).__init__(*args, **kwargs)

    @staticmethod
    def _set_cookies(cookies_raw):
        cookies = {}
        if cookies_raw is None:
            return cookies
        cookies_str = str(cookies_raw)
        for cookie in re.findall(r'Set-Cookie: (.*?)=(.*?); Domain', cookies_str, re.S):
            cookies[cookie[0]] = cookie[1]
        return cookies

    def _set_url(self, url):
        if isinstance(url, str):
            self._url = to_unicode(url, self.encoding)
        else:
            super(TextResponse, self)._set_url(url)

    def _set_body(self, body):
        self._body = b''  # used by encoding detection
        if isinstance(body, str):
            if self._encoding is None:
                raise TypeError('Cannot convert unicode body - %s has no encoding' %
                                type(self).__name__)
            self._body = body.encode(self._encoding)
        else:
            super(TextResponse, self)._set_body(body)

    def replace(self, *args, **kwargs):
        kwargs.setdefault('encoding', self.encoding)
        return Response.replace(self, *args, **kwargs)

    @property
    def encoding(self):
        return self._declared_encoding() or self._body_inferred_encoding()

    def _declared_encoding(self):
        return self._encoding or self._headers_encoding() \
            or self._body_declared_encoding()

    def body_as_unicode(self):
        """Return body as unicode"""
        return self.text

    @property
    def text(self):
        """ Body as unicode """
        # access self.encoding before _cached_ubody to make sure
        # _body_inferred_encoding is called
        benc = self.encoding
        if self._cached_ubody is None:
            charset = 'charset=%s' % benc
