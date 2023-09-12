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
    def load_all_spider(dirname):
        _class_objects = {}
    
        def load_all_spider_inner(dirname):
            for importer, package_name, ispkg in iter_modules([dirname]):
                if ispkg:
                    load_all_spider_inner(dirname + '/' + package_name)
                else:
                    module = importer.find_module(package_name)
                    module = module.load_module(package_name)
                    for cls_name in module.__dir__():
                        if cls_name == "__spiders__":
                            class_object = getattr(module, cls_name)
                            for co in class_object:
                                _class_objects[co.name] = co
                        if not cls_name.startswith('__'):
                            class_object = getattr(module, cls_name)
                            if hasattr(class_object, "name") and getattr(class_object, "name"):
                                _class_objects[class_object.name] = class_object


        load_all_spider_inner(dirname)
        return _class_objects

    @staticmethod
    def load_object(path: str):
        try:
            dot = path.rindex('.')
        except ValueError:
            raise ValueError("Error loading object '%s': not a full path" % path)

        module, name = path[:dot], path[dot + 1:]
        mod = import_module(module)

        try:
            obj = getattr(mod, name)
        except AttributeError:
            raise NameError("Module '%s' doesn't define any object named '%s'" % (module, name))
        else:
            return obj

    def load_object_slot(self, key: str, path: str, cls=None):
        obj = self.load_object(path)
        if cls is None:
            obj = self.create_instance(obj, self.settings, self.crawler)
            self.slot.set(key, obj)
        else:
            self.c_slot.set(key, obj)
        return obj

    def walk_modules(self, path: str):
        mods = []
        if hasattr(self, "slot"):
            mods = self.slot._modules_slot
        mod = import_module(path)
        mods.append(mod)
        if hasattr(mod, '__path__'):
            for _, subpath, ispkg in iter_modules(mod.__path__):
                fullpath = path + '.' + subpath
                if ispkg:
                    mods += self.walk_modules(fullpath)
                else:
                    submod = import_module(fullpath)
                    mods.append(submod)
        return mods

    def create_instance(self, objcls, settings, crawler, *args, **kwargs):
        if settings is None:
            if crawler is None:
                raise ValueError("Specify at least one of settings and crawler.")
            settings = crawler.settings
        if not (type(objcls) == "function"):
            objcls = call_grace_instance(objcls, only_instance=True)
        if crawler and hasattr(objcls, 'from_crawler'):
            return objcls.from_crawler(crawler, *args, **kwargs)
        elif hasattr(objcls, 'from_settings'):
