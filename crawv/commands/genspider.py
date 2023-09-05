import os
import shutil
import string

from importlib import import_module
from os.path import join, dirname, abspath, exists, splitext

import crawv
from crawv.commands import ASCommand
from crawv.utils.template import render_templatefile, string_camelcase
from crawv.exceptions import UsageError


def sanitize_module_name(module_name):
    """Sanitize the given module name, by replacing dashes and points
    with underscores and prefixing it with a letter if it doesn't start
    with one
    """
    module_name = module_name.replace('-', '_').replace('.', '_')
    if module_name[0] not in string.ascii_letters:
        module_name = "a" + module_name
    return module_name


class Command(ASCommand):

    requires_project = False
    default_settings = {'LOG_ENABLED': False}
    requires_process = False

    def syntax(self):
        return "[options] <name>"

    def short_desc(self):
        return "Generate new spider in project using pre-defined templates"

    def add_options(self, parser):
        ASCommand.add_options(self, parser)
        parser.add_argument("-l", "--list", dest="list", action="store_true",
                            help="List available templates")
        parser.add_argument("-d", "--dump", dest="dump", metavar="TEMPLATE",
                            help="Dump template to standard output")
        parser.add_argument("-t", "--template", dest="template", default="basic",
                            help="Uses a custom template.")
        parser.add_argument("--force", dest="force", action="store_true",
                            help="If the spider already exists, overwrite it with the template")

    def run(self, args, opts):
        if opts.list:
            self._list_templates()
            return
        if opts.dump:
            template_file = self._find_template(opts.dump)
            if template_file:
                with open(template_file, "r") as f:
                    print(f.read())
            return
        if not args:
            raise UsageError()

        name = args[0]
        module = sanitize_module_name(name)

        if self.settings.get('BOT_NAME') == module:
            print("Cannot create a spider with the same name as your project")
            return

        if not opts.force and self._spider_exists(name):
            return

        template_file = self._find_template(opts.template)
        if template_file:
            self._genspider(module, name, opts.template, template_file)

    def _genspider(self, module, name, template_name, template_file):
        """Generate the spider module, based on the given template"""
