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
    """Return the binary representation of ``text``. If ``text``
    is already a bytes object, return it as-is."""
    if isinstance(text, bytes):
        return text
    if not isinstance(text, str):
        raise TypeError('to_bytes must receive a str or bytes '
                        'object, got %s' % type(text).__name__)
    if encoding is None:
        encoding = 'utf-8'
    return text.encode(encoding, errors)


async def call_helper(f, *args, **kwargs):
    if asyncio.iscoroutinefunction(f):
        return await f(*args, **kwargs)
    return f(*args, **kwargs)


async def async_generator_wrapper(wrapped):
    """å°†ä¼ å…¥çš„å¯¹è±¡å˜æˆAsyncGeneratorTypeç±»åž‹"""
    if isinstance(wrapped, AsyncGeneratorType):
        return wrapped

    elif isinstance(wrapped, CoroutineType):
        async def anonymous(c):
            yield await c
        return anonymous(wrapped)

    elif isinstance(wrapped, GeneratorType):
        async def anonymous(c):
            for r in c:
                yield r
        return anonymous(wrapped)

    else:
        async def anonymous(c):
            yield c
        return anonymous(wrapped)


def closest_crawv_cfg(path='.', prevpath=None):
    """Return the path to the closest crawv.cfg file by traversing the current
    directory and its parents
    """
    if path == prevpath:
        return ''
    path = os.path.abspath(path)
    cfgfile = os.path.join(path, 'crawv.cfg')
    if os.path.exists(cfgfile):
        return cfgfile
    return closest_crawv_cfg(os.path.dirname(path), path)


def get_sources(use_closest=True):
    xdg_config_home = os.environ.get('XDG_CONFIG_HOME') or os.path.expanduser('~/.config')
    sources = [
        '/etc/crawv.cfg',
        r'c:\crawv\crawv.cfg',
        xdg_config_home + '/crawv.cfg',
        os.path.expanduser('~/.crawv.cfg'),
    ]
    if use_closest:
        sources.append(closest_crawv_cfg())
    return sources


def get_config(use_closest=True):
    """Get Crawv config file as a ConfigParser"""
    sources = get_sources(use_closest)
    cfg = ConfigParser()
    cfg.read(sources)
    return cfg


def init_env(project='default', set_syspath=True):
    """Initialize environment to use command-line tool from inside a project
    dir. This sets the Crawv settings module and modifies the Python path to
    be able to locate the project module.
    """
    cfg = get_config()
    if cfg.has_option('settings', project):
        os.environ['SETTINGS_MODULE'] = cfg.get('settings', project)
    if cfg.has_option('package_env', "path"):
        path = cfg.get('package_env', 'path')
        sys.path.append(path)
    closest = closest_crawv_cfg()
    if closest:
        projdir = os.path.dirname(closest)
        if set_syspath and projdir not in sys.path:
            sys.path.append(projdir)


def get_project_settings():

    ENVVAR = 'SETTINGS_MODULE'

    if ENVVAR not in os.environ:
        project = os.environ.get('CRAWV_PROJECT', 'default')
        init_env(project)
    settings = Settings()
    settings_module_path = os.environ.get(ENVVAR)
    if settings_module_path:
        settings.setmodule(settings_module_path, priority='project')

    crawv_envvars = {k[8:]: v for k, v in os.environ.items() if
                      k.startswith('CRAWV_')}
    valid_envvars = {
        'CHECK',
        'PROJECT',
        'PYTHON_SHELL',
        'SETTINGS_MODULE',
    }
    setting_envvars = {k for k in crawv_envvars if k not in valid_envvars}
    if setting_envvars:
        setting_envvar_list = ', '.join(sorted(setting_envvars))
        warnings.warn(
            'Use of environment variables prefixed with CRAWV_ to override '
            'settings is deprecated. The following environment variables are '
            f'currently defined: {setting_envvar_list}',
            CrawvDeprecationWarning
        )
    settings.setdict(crawv_envvars, priority='project')
    settings['DI_CONFIG']['scheduler'] = settings['SCHEDULER']
    settings['DI_CREATE_CLS']['downloader_handler'] = settings['DOWNLOAD_HANDLER']
    return settings


def singleton(cls):
    _instance = {}

    def _singleton(*args, **kwargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)
        return _instance[cls]

    return _singleton


def exec_js_func(js_file_path, func_name, func_params=None, cwd_path=None, cmd_path='node'):
    """
    è°ƒç”¨nodeæ‰§è¡Œjsæ–‡ä»¶
    :param js_file_path: jsæ–‡ä»¶è·¯å¾„
    :param func_name: è¦è°ƒç”¨çš„jsæ–‡ä»¶å†…çš„å‡½æ•°åç§°
    :param func_params: funcçš„å‚æ•°
    :param cwd_path: node_modulesæ–‡ä»¶æ‰€åœ¨è·¯å¾„ï¼Œå¦‚æžœä¸æŒ‡å®šå°†ä½¿ç”¨å…¨å±€çš„node_modules
    :param cmd_path: nodeçš„ä½ç½®ï¼Œ ä¾‹å¦‚ï¼šr'D:\\path\to\node.exe'
    :return: func_nameå‡½æ•°çš„æ‰§è¡Œç»“æžœ
    """
    import execjs

    if func_params is None:
        func_params = []
