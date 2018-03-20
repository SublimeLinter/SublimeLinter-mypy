#
# linter.py
# Linter for SublimeLinter3, a code checking framework for Sublime Text 3
#
# Written by Fred Callaway
# Copyright (c) 2015 Fred Callaway
# Copyright (c) 2017 FichteFoll <fichtefoll2@googlemail.com>
#
# License: MIT
#

"""This module exports the Mypy plugin class."""

import logging
import os
import shutil
import tempfile
import re

from SublimeLinter.lint import const
from SublimeLinter.lint import PythonLinter, util


TMPDIR_PREFIX = "SublimeLinter-contrib-mypy-"

logger = logging.getLogger("SublimeLinter.plugin.mypy")

# Mapping for our created temporary directories.
# For smarter caching purposes,
# we index different cache folders based on the working dir.
tmpdirs = {}


class Mypy(PythonLinter):
    """Provides an interface to mypy."""

    executable = "mypy"
    regex = r'^[^:]+:(?P<line>\d+):((?P<col>\d+):)?\s*((?P<error>error)|(?P<warning>warning)):\s*(?P<message>.+)'
    version_re = r'(?P<version>\d+\.\d+(\.\d+)?)'
    line_col_base = (1, 0)
    tempfile_suffix = 'py'
    default_type = const.WARNING

    # Pretty much all interesting options don't expect a value,
    # so you'll have to specify those in "args" anyway.
    # This dict only contains settings for which we have special handling.
    defaults = {
        # Will default to tempfile.TemporaryDirectory if empty.
        "--cache-dir:": "",
        # Need this to silent lints for other files. Alternatively: 'skip'
        "--follow-imports:": "silent",
        'selector': "source.python",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        version = float(self._get_version())
        if version >= 0.57:
            self.line_col_base = (1, 1)

    def cmd(self):
        """Return a list with the command line to execute."""
        cmd = [
            self.executable,
            '*',
            '--show-column-numbers',
            '--hide-error-context',
            '--incremental',
        ]
        if self.filename:
            cmd.extend([
                # --shadow-file SOURCE_FILE SHADOW_FILE
                #
                # '@' needs to be the (temporary) shadow file,
                # while we request the normal filename
                # to be checked in its normal environment.
                '--shadow-file', self.filename, '@',
                # The file we want to lint on the surface
                self.filename
            ])
        else:
            cmd.append('@')

        # Add a temporary cache dir to the command if none was specified.
        # Helps keep the environment clean
        # by not littering everything with `.mypy_cache` folders.
        settings = self.get_view_settings()
        if not settings.get('cache-dir'):
            cwd = os.getcwd()
            if cwd in tmpdirs:
                cache_dir = tmpdirs[cwd].name
            else:
                tmp_dir = tempfile.TemporaryDirectory(prefix=TMPDIR_PREFIX)
                tmpdirs[cwd] = tmp_dir
                cache_dir = tmp_dir.name
                logger.debug("Created temporary cache dir at: %s", cache_dir)
            cmd[1:1] = ["--cache-dir", cache_dir]

        return cmd

    def _get_version(self):
        """Return installed mypy version as a string."""
        output = util.communicate(self.executable + ' --version')
        version = re.findall(self.version_re, str(output))[0][0]
        return version


def _cleanup_tmpdirs():
    def _onerror(function, path, exc_info):
        logger.exception("mypy: Unable to delete '%s' while cleaning up temporary directory", path,
                         exc_info=exc_info)
    tmpdir = tempfile.gettempdir()
    for dirname in os.listdir(tmpdir):
        if dirname.startswith(TMPDIR_PREFIX):
            shutil.rmtree(os.path.join(tmpdir, dirname), onerror=_onerror)


def plugin_loaded():
    """Attempt to clean up temporary directories from previous runs."""
    _cleanup_tmpdirs()


def plugin_unloaded():
    """Clear references to TemporaryDirectory instances.

    They should then be removed automatically.
    """
    # (Actually, do we even need to do this?)
    tmpdirs.clear()
