import os
import argparse
from typing import Any, Dict


from crawv.utils.common import arglist_to_dict
from crawv.exceptions import UsageError


class ASCommand:

    requires_project = False
    crawler_process = None
    requires_process = True

    # default settings to be used for this command instead of global defaults
    default_settings: Dict[str, Any] = {}

    exitcode = 0

    def __init__(self):
        self.settings = None  # set in crawv.cmdline

    def set_crawler(self, crawler):
        if hasattr(self, '_crawler'):
            raise RuntimeError("crawler already set")
        self._crawler = crawler

    def syntax(self):
        """
        Command syntax (preferably one-line). Do not include command name.
        """
        return ""

    def short_desc(self):
        """
        A short description of the command
        """
        return ""

    def long_desc(self):
        """A long description of the command. Return short description when not
        available. It cannot contain newlines since contents will be formatted
        by optparser which removes newlines and wraps text.
        """
        return self.short_desc()

    def help(self):
        """An extensive help for the command. It will be shown when using the
        "help" command. It can contain newlines since no post-formatting will
        be applied to its contents.
        """
        return self.long_desc()

    def add_options(self, parser):
        """
        Populate option parse with options available for this command
        """
        group = parser.add_argument_group(title='Global Options')
        group.add_argument("--logfile", metavar="FILE",
                           help="log file. if omitted stderr will be used")
        group.add_argument("-L", "--loglevel", metavar="LEVEL", default=None,
                           help=f"log level (default: {self.settings['LOG_LEVEL']})")
        group.add_argument("--nolog", action="store_true",
                           help="disable logging completely")
        group.add_argument("--profile", metavar="FILE", default=None,
                           help="write python cProfile stats to FILE")
        group.add_argument("--pidfile", metavar="FILE",
                           help="write process ID to FILE")
        group.add_argument("-s", "--set", action="append", default=[], metavar="NAME=VALUE",
                           help="set/override setting (may be repeated)")

    def process_options(self, args, opts):
        try:
            self.settings.setdict(arglist_to_dict(opts.set),
                                  priority='cmdline')
