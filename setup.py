import os
import sys
from shutil import rmtree
from os.path import dirname, join

from setuptools import setup, Command, find_packages

# Package meta-data.
NAME = "crawv"
DESCRIPTION = "Crawv: an asyncio crawler framework inspired by Scrapy"
URL = "https://github.com/seme555/crawv"
EMAIL = "semeabe@gmail.com"
AUTHOR = "Semere Abera"
REQUIRES_PYTHON = ">=3.8.0"

here = os.path.abspath(os.path.dirname(__file__))
with open(f"{here}/README.md", encoding='utf-8') as f:
    long_description = f.read()

with open(join(dirname(__file__), 'crawv/VERSION'), 'rb') as f:
    old_version = f.read().decode('ascii').strip()
    maxv, midv, minv = [int(v) for v in old_version.split('.')]
    if minv <= 24:
        minv += 1
    else:
        midv += 1
        minv = 0
    VERSION = '.'.join([str(v) for v in [maxv, midv, minv]])
    print(f'old version: {old_version}, new version: {VERSION}')


class UploadCommand(Command):
    """Support setup_bak.py upload."""

    description = "Build and publish the package."
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print("\033[1m{0}\033[0m".format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status("Removing previous builds...")
            rmtree(os.path.join(here, "dist"))
        except OSError:
            pass

        self.status("Building Source and Wheel distribution...")
        os.system("{0} setup.py sdist bdist_wheel".format(sys.executable))

        self.status("Uploading the package to PyPI via Twine...")
        os.system("twine upload dist/*")

        with open(join(dirname(__file__), 'crawv/VERSION'), 'w') as f:
            f.write(VERSION + '\n')

        self.status("git option [add]")
        os.system("git add crawv/VERSION")

        self.status("git option [commit][push]")
        os.system(f'git commit -m "{VERSION}"')
        os.system("git push")
        sys.exit()


extras_require = {
    "all": [
        "aiohttp",
