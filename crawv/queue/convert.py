"""
Helper functions for serializing (and deserializing) requests.
"""
import inspect
import json

from crawv import call_grace_instance
from crawv.http import Request
from crawv.utils.tools import to_unicode
from crawv.inject import load_object
from anti_header import Headers


def request_to_dict(request, spider=None):
    """Convert Request object to a dict.

    If a spider is given, it will try to find out the name of the spider method
    used in the callback and store that as the callback.
    """
    cb = request.callback
    if callable(cb):
        cb = _find_method(spider, cb)
    eb = request.errback
    if callable(eb):
        eb = _find_method(spider, eb)
    d = {
        'url': to_unicode(request.url),  # urls should be safe (safe_string_url)
        'callback': cb,
        'errback': eb,
        'method': request.method,
        'headers': dict(request.headers),
        'body': request.body,
        'json': request.json,
        'cookies': request.cookies,
        'meta': request.meta,
        '_encoding': request._encoding,
        'priority': request.priority,
        'dont_filter': request.dont_filter,
        'flags': request.flags,
        'cb_kwargs': request.cb_kwargs,
    }
    _body = getattr(request, "body")
    _json = getattr(request, "json")
    if _body and isinstance(_body, dict) or _json and isinstance(_json, dict):
        base_cls = request.__class__.__bases__[0]
        d['_class'] = base_cls.__module__ + '.' + base_cls.__name__
    return d


def request_from_dict(d, spider=None):
    """Create Request object from a dict.

    If a spider is given, it will try to resolve the callbacks looking at the
    spider for methods with the same name.
    """
    cb = d.get('callback', 'parse')
    if cb and spider:
        cb = _get_method(spider, cb)
    eb = d.get('errback')
    if eb and spider:
        eb = _get_method(spider, eb)
    request_cls = load_object(d['_class']) if '_class' in d else Request

    _json, _body = None, None
    if request_cls.__name__ in ["FormRequest"]:
        if d.get('body') and isinstance(d.get('body'), dict):
            _body = d['body']
        elif d.get('body') and isinstance(d.get('body'), str):
            _body = json.loads(d['body'])
    elif request_cls.__name__ in ["JsonRequest"]:
        if d.get('json') and isinstance(d.get('json'), dict):
            _json = d['json']
        elif d.get('json') and isinstance(d.get('json'), str):
            _json = json.loads(d['json'])

    return call_grace_instance(
