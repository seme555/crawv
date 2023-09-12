import asyncio

from importlib import import_module
from pkgutil import iter_modules

from crawv.settings import Settings
from crawv.utils.tools import singleton, get_project_settings


@singleton
class CSlot:

    def __init__(self):
        self._object_slot_cls = {}

    def get(self, sets: str, default=None) -> object:
        return self._object_slot_cls.get(sets, default)

    def set(self, sets: str, obj: object):
        self._object_slot_cls.__setitem__(sets, obj)

    def empty(self):
        return not bool(len(self._object_slot_cls))


class Slot:

    def __init__(self, settings, crawler):
        self._objects_slot = {
            'settings': settings,
            'crawler': crawler
        }
        self._modules_slot = []
        self._close = None
        self.live_beat = None

    @property
    def is_live(self):
        return bool(self._close)

    def get(self, sets: str, default=None) -> object:
        return self._objects_slot.get(sets, default)

    def set(self, sets: str, obj: object):
        self._objects_slot.__setitem__(sets, obj)

    def clear(self):
        del self._objects_slot
        self._modules_slot = []
        self._close = True

    def close(self):
        if self.live_beat:
            self.live_beat.cancel()


class DependencyInjection(object):
    def __init__(self, settings: Settings = None, crawler=None):
        if not settings:
            settings = Settings()
        self.settings = settings
        self.crawler = crawler
        self.slot = Slot(settings, crawler)

    @classmethod
    def from_settings(cls, settings, crawler):
        return cls(settings, crawler)

    @classmethod
    def from_crawler(cls, crawler):
        return cls.from_settings(crawler.settings, crawler)

    def load(self, key: str):
        return self.slot.get(key)

    @staticmethod
