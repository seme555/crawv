import json
import copy

from collections.abc import MutableMapping
from importlib import import_module
from pprint import pformat

from . import default_settings


SETTINGS_PRIORITIES = {
    'default': 0,
    'command': 10,
    'project': 20,
    'spider': 30,
    'cmdline': 40,
}


def get_settings_priority(priority):
    """
    Small helper function that looks up a given string priority in the
    :attr:`~crawv.settings.SETTINGS_PRIORITIES` dictionary and returns its
    numerical value, or directly returns a given numerical priority.
    """
    if isinstance(priority, str):
        return SETTINGS_PRIORITIES[priority]
    else:
        return priority


class SettingsAttribute:

    """Class for storing data related to settings attributes.

    This class is intended for internal usage, you should try Settings class
    for settings configuration, not this one.
    """

    def __init__(self, value, priority):
        self.value = value
        if isinstance(self.value, BaseSettings):
            self.priority = max(self.value.maxpriority(), priority)
        else:
            self.priority = priority

    def set(self, value, priority):
        """Sets value if priority is higher or equal than current priority."""
        if priority >= self.priority:
            if isinstance(self.value, BaseSettings):
                value = BaseSettings(value, priority=priority)
            self.value = value
            self.priority = priority

    def __str__(self):
        return f"<SettingsAttribute value={self.value!r} priority={self.priority}>"

    __repr__ = __str__


class BaseSettings(MutableMapping):
    """
    Instances of this class behave like dictionaries, but store priorities
    along with their ``(key, value)`` pairs, and can be frozen (i.e. marked
    immutable).

    Key-value entries can be passed on initialization with the ``values``
    argument, and they would take the ``priority`` level (unless ``values`` is
    already an instance of :class:`~crawv.settings.BaseSettings`, in which
    case the existing priority levels will be kept).  If the ``priority``
    argument is a string, the priority name will be looked up in
    :attr:`~crawv.settings.SETTINGS_PRIORITIES`. Otherwise, a specific integer
    should be provided.

    Once the object is created, new settings can be loaded or updated with the
    :meth:`~crawv.settings.BaseSettings.set` method, and can be accessed with
    the square bracket notation of dictionaries, or with the
    :meth:`~crawv.settings.BaseSettings.get` method of the instance and its
    value conversion variants. When requesting a stored key, the value with the
    highest priority will be retrieved.
    """

    def __init__(self, values=None, priority='project'):
        self.frozen = False
        self.attributes = {}
        if values:
            self.update(values, priority)

    def __getitem__(self, opt_name):
        if opt_name not in self:
            return None
        return self.attributes[opt_name].value

    def __contains__(self, name):
        return name in self.attributes

    def get(self, name, default=None):
        """
        Get a setting value without affecting its original type.

        :param name: the setting name
        :type name: str

        :param default: the value to return if no setting is found
        :type default: object
        """
        return self[name] if self[name] is not None else default

    def getbool(self, name, default=False):
        """
        Get a setting value as a boolean.

        ``1``, ``'1'``, `True`` and ``'True'`` return ``True``,
        while ``0``, ``'0'``, ``False``, ``'False'`` and ``None`` return ``False``.

        For example, settings populated through environment variables set to
        ``'0'`` will return ``False`` when using this method.

        :param name: the setting name
        :type name: str

        :param default: the value to return if no setting is found
        :type default: object
        """
        got = self.get(name, default)
        try:
            return bool(int(got))
        except ValueError:
            if got in ("True", "true"):
                return True
            if got in ("False", "false"):
                return False
            raise ValueError("Supported values for boolean settings "
                             "are 0/1, True/False, '0'/'1', "
                             "'True'/'False' and 'true'/'false'")

    def getint(self, name, default=0):
        """
        Get a setting value as an int.

        :param name: the setting name
        :type name: str

        :param default: the value to return if no setting is found
        :type default: object
        """
        return int(self.get(name, default))

    def getfloat(self, name, default=0.0):
        """
        Get a setting value as a float.

        :param name: the setting name
        :type name: str

        :param default: the value to return if no setting is found
        :type default: object
        """
        return float(self.get(name, default))

    def getlist(self, name, default=None):
        """
        Get a setting value as a list. If the setting original type is a list, a
        copy of it will be returned. If it's a string it will be split by ",".

        For example, settings populated through environment variables set to
        ``'one,two'`` will return a list ['one', 'two'] when using this method.

        :param name: the setting name
        :type name: str

        :param default: the value to return if no setting is found
        :type default: object
        """
        value = self.get(name, default or [])
        if isinstance(value, str):
            value = value.split(',')
        return list(value)

    def getdict(self, name, default=None):
        """
        Get a setting value as a dictionary. If the setting original type is a
        dictionary, a copy of it will be returned. If it is a string it will be
        evaluated as a JSON dictionary. In the case that it is a
        :class:`~crawv.settings.BaseSettings` instance itself, it will be
        converted to a dictionary, containing all its current settings values
        as they would be returned by :meth:`~crawv.settings.BaseSettings.get`,
        and losing all information about priority and mutability.

        :param name: the setting name
        :type name: str

        :param default: the value to return if no setting is found
        :type default: object
        """
        value = self.get(name, default or {})
        if isinstance(value, str):
            value = json.loads(value)
        return dict(value)

    def getwithbase(self, name):
        """Get a composition of a dictionary-like setting and its `_BASE`
        counterpart.

        :param name: name of the dictionary-like setting
        :type name: str
        """
        compbs = BaseSettings()
        compbs.update(self[name + '_BASE'])
        compbs.update(self[name])
        return compbs

    def getpriority(self, name):
        """
        Return the current numerical priority value of a setting, or ``None`` if
        the given ``name`` does not exist.

        :param name: the setting name
        :type name: str
        """
        if name not in self:
            return None
        return self.attributes[name].priority

    def maxpriority(self):
        """
        Return the numerical value of the highest priority present throughout
        all settings, or the numerical value for ``default`` from
