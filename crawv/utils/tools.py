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
