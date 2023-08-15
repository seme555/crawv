import ujson
import json
import asyncio
import weakref
import sys
import os
import pickle
import warnings

from configparser import ConfigParser
from typing import Dict, Iterable, Optional, Tuple, Union
from functools import wraps
from asyncio import events
from types import CoroutineType, GeneratorType, AsyncGeneratorType

from crawv.settings import Settings
from crawv.exceptions import CrawvDeprecationWarning


async def call_create_task(f, *args, **kwargs):
    try:
        if events._get_running_loop():
            await call_helper(asyncio.create_task, f(*args, **kwargs))
    except:
        pass


async def task_await(cls, *args):
    while not all([getattr(cls, arg, None) for arg in args]):
        await asyncio.sleep(0.5)


def install_event_loop_tips():
    if sys.version_info[:2] == (3, 7):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    else:
        try:
            import uvloop
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        except:
            pass
    setattr(asyncio.sslproto._SSLProtocolTransport, "_start_tls_compatible", True)


def referer_str(request) -> Optional[str]:
    """ Return Referer HTTP header suitable for logging. """
    referrer = request.headers.get('Referer')
    if referrer is None:
        return referrer
    return to_unicode(referrer, errors='replace')


def method_is_overridden(subclass, base_class, method_name):
    """
    Return True if a method named ``method_name`` of a ``base_class``
    is overridden in a ``subclass``.

    >>> class Base(object):
    ...     def foo(self):
    ...         pass
    >>> class Sub1(Base):
    ...     pass
    >>> class Sub2(Base):
    ...     def foo(self):
    ...         pass
    >>> class Sub3(Sub1):
    ...     def foo(self):
    ...         pass
    >>> class Sub4(Sub2):
    ...     pass
    >>> method_is_overridden(Sub1, Base, 'foo')
    False
    >>> method_is_overridden(Sub2, Base, 'foo')
    True
    >>> method_is_overridden(Sub3, Base, 'foo')
    True
    >>> method_is_overridden(Sub4, Base, 'foo')
    True
    """
    base_method = getattr(base_class, method_name)
    sub_method = getattr(subclass, method_name)
    return base_method.__code__ is not sub_method.__code__


def memoizemethod_noargs(method):
    """Decorator to cache the result of a method (without arguments) using a
    weak reference to its object
    """
    cache = weakref.WeakKeyDictionary()

    @wraps(method)
    def new_method(self, *args, **kwargs):
        if self not in cache:
            cache[self] = method(self, *args, **kwargs)
        return cache[self]
    return new_method


def is_listlike(x):
    """
    >>> is_listlike("foo")
    False
    >>> is_listlike(5)
    False
    >>> is_listlike(b"foo")
    False
    >>> is_listlike([b"foo"])
    True
    >>> is_listlike((b"foo",))
    True
    >>> is_listlike({})
    True
    >>> is_listlike(set())
    True
    >>> is_listlike((x for x in range(3)))
    True
    >>> is_listlike(range(5))
    True
    """
    return hasattr(x, "__iter__") and not isinstance(x, (str, bytes))


def unique(list_, key=lambda x: x):
    """efficient function to uniquify a list preserving item order"""
    seen = set()
    result = []
    for item in list_:
        seenkey = key(item)
        if seenkey in seen:
            continue
        seen.add(seenkey)
        result.append(item)
    return result


def to_unicode(text, encoding=None, errors='strict'):
    """Return the unicode representation of a bytes object ``text``. If
    ``text`` is already an unicode object, return it as-is."""
    if isinstance(text, str):
        return text
    if not isinstance(text, (bytes, str)):
        raise TypeError('to_unicode must receive a bytes or str '
                        'object, got %s' % type(text).__name__)
    if encoding is None:
        encoding = 'utf-8'
    return text.decode(encoding, errors)


def to_bytes(text, encoding=None, errors='strict'):
