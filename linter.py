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

import os
import shutil
import tempfile

from SublimeLinter.lint import PythonLinter, util, highlight, persist

TMPDIR_PREFIX = "SublimeLinter-contrib-mypy-"

# Mapping for our created temporary directories.
# For smarter caching purposes,
# we index different cache folders based on the working dir.
tmpdirs = {}


class Mypy(PythonLinter):
    """Provides an interface to mypy."""

    syntax = 'python'
    executable = "mypy"
    version_args = '--version'
    version_re = r'(?P<version>\d+\.\d+(\.\d+)?)'
    version_requirement = '>= 0.520'
    check_version = True

    regex = r'^[^:]+:(?P<line>\d+):((?P<col>\d+):)?\s*((?P<error>error)|(?P<warning>warning)):\s*(?P<message>.+)'
    error_stream = util.STREAM_BOTH
    line_col_base = (1, 0)
    # multiline = False

    tempfile_suffix = 'py'
    config_file = ('--config-file', 'mypy.ini')

    # Pretty much all interesting options don't expect a value,
    # so you'll have to specify those in "args" anyway.
    # This dict only contains settings for which we have special handling.
    defaults = {
        # Will default to tempfile.TemporaryDirectory if empty.
        "--cache-dir": "",
    }
    default_type = highlight.WARNING
    # selectors = {}
    # word_re = None

    def cmd(self):
        """Return a list with the command line to execute."""
        cmd = [
            self.executable,
            '*',
            '--show-column-numbers',
            '--hide-error-context',
            '--incremental',
            # --shadow-file SOURCE_FILE SHADOW_FILE
            #
            # '@' needs to be the (temporary) shadow file,
            # while we request the normal filename
            # to be checked in its normal environment.
            '--shadow-file', self.filename, '@',
            # The file we want to lint on the surface
            self.filename
        ]

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
                persist.debug("Created temporary cache dir at: " + cache_dir)
            cmd[1:1] = ["--cache-dir", cache_dir]

        return cmd


def _cleanup_tmpdirs():
    def _onerror(function, path, excinfo):
        persist.printf("mypy: Unable to delete '{}' while cleaning up temporary directory".format(path))
        import traceback
        traceback.print_exc(*excinfo)
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
