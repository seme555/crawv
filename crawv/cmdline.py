import sys
import os
import argparse
import cProfile
import inspect
import pkg_resources

import crawv
from crawv.inject import walk_modules
from crawv.commands import ASCommand, ASHelpFormatter
from crawv.exceptions import UsageError
from crawv.utils.tools import get_project_settings
from crawv.utils.common import inside_project
from crawv import call_grace_instance


def _iter_command_classes(module_name):
    # TODO: add `name` attribute to commands and and merge this function with
    for module in walk_modules(module_name):
        for obj in vars(module).values():
            if (
                inspect.isclass(obj)
                and issubclass(obj, ASCommand)
                and obj.__module__ == module.__name__
                and not obj == ASCommand
            ):
                yield obj


def _get_commands_from_module(module, inproject):
    d = {}
    for cmd in _iter_command_classes(module):
        if inproject or not cmd.requires_project:
            cmdname = cmd.__module__.split('.')[-1]
            d[cmdname] = cmd()
    return d


def _get_commands_from_entry_points(inproject, group='crawv.commands'):
    cmds = {}
    for entry_point in pkg_resources.iter_entry_points(group):
        obj = entry_point.load()
        if inspect.isclass(obj):
            cmds[entry_point.name] = obj()
        else:
            raise Exception(f"Invalid entry point {entry_point.name}")
    return cmds


def _get_commands_dict(settings, inproject):
    cmds = _get_commands_from_module('crawv.commands', inproject)
    cmds.update(_get_commands_from_entry_points(inproject))
    cmds_module = settings['COMMANDS_MODULE']
    if cmds_module:
        cmds.update(_get_commands_from_module(cmds_module, inproject))
    return cmds


def _pop_command_name(argv):
    i = 0
    for arg in argv[1:]:
        if not arg.startswith('-'):
            del argv[i]
            return arg
        i += 1


def _print_header(settings, inproject):
    version = crawv.__version__
    if inproject:
        print(f"crawv {version} - project: {settings['BOT_NAME']}\n")
    else:
        print(f"crawv {version} - no active project\n")


def _print_commands(settings, inproject):
