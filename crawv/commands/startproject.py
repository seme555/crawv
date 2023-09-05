import re
import os
import string
from importlib.util import find_spec
from os.path import join, exists, abspath
from shutil import ignore_patterns, move, copy2, copystat
from stat import S_IWUSR as OWNER_WRITE_PERMISSION

import crawv
from crawv.commands import ASCommand
from crawv.utils.template import render_templatefile, string_camelcase
from crawv.exceptions import UsageError


TEMPLATES_TO_RENDER = (
    ('crawv.cfg',),
    ('settings.py.tmpl',),
    ('pipelines.py.tmpl',),
    ('middlewares.py.tmpl',),
    ('start.py.tmpl',),
)

IGNORE = ignore_patterns('*.pyc', '__pycache__', '.svn')


def _make_writable(path):
    current_permissions = os.stat(path).st_mode
    os.chmod(path, current_permissions | OWNER_WRITE_PERMISSION)


class Command(ASCommand):

    requires_project = False
    default_settings = {'LOG_ENABLED': False,
                        'SPIDER_LOADER_WARN_ONLY': True}
    requires_process = False

    def syntax(self):
        return "<project_name> [project_dir]"

    def short_desc(self):
        return "Create new project"

    def _is_valid_name(self, project_name):
        def _module_exists(module_name):
            spec = find_spec(module_name)
            return spec is not None and spec.loader is not None

        if not re.search(r'^[_a-zA-Z]\w*$', project_name):
            print('Error: Project names must begin with a letter and contain'
                  ' only\nletters, numbers and underscores')
        elif _module_exists(project_name):
            print(f'Error: Module {project_name!r} already exists')
        else:
            return True
        return False

    def _copytree(self, src, dst):
        """
        Since the original function always creates the directory, to resolve
        the issue a new function had to be created. It's a simple copy and
        was reduced for this case.

        More info at:
        https://github.com/crawv/crawv/pull/2005
        """
        ignore = IGNORE
        names = os.listdir(src)
        ignored_names = ignore(src, names)

        if not os.path.exists(dst):
            os.makedirs(dst)

        for name in names:
            if name in ignored_names:
                continue
