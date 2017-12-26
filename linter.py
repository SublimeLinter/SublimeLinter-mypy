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
tmpdirs = {}  # type: Dict[str, tempfile.TemporaryDirectory]


class Mypy(PythonLinter):
    """Provides an interface to mypy."""

    syntax = 'python'
    version_args = '--version'
    version_re = r'(?P<version>\d+\.\d+(\.\d+)?)'
    version_requirement = '>= 0.520'

    regex = r'^.+\.py:(?P<line>\d+):(?P<col>\d+): error: (?P<message>.+)'
    error_stream = util.STREAM_BOTH
    line_col_base = (1, 0)
    # multiline = False

    # mypy takes quite some time, so we only do it on saved files.
    # If you want it for unsaved files as well,
    # uncomment the second line below.
    tempfile_suffix = 'py'
    tempfile_suffix = '-'
    config_file = ('--config-file', 'mypy.ini')

    # Pretty much all interesting options don't expect a value,
    # so you'll have to specify those in "args".
    # The following are mostly provided
    # because of their usage for inline settings/overrides.
    defaults = {
        "--strict-optional-whitelist: ": [],
        "--disallow-any:,": [],
        "--python-version": "",
        # Will default to tempfile.TemporaryDirectory if empty.
        "--cache-dir": "",
        "--config-file": "",
    }
    default_type = highlight.WARNING
    inline_settings = (
        "python-version",
    )
    inline_overrides = (
        "disallow-any",
        "strict-optional-whitelist",
    )
    # selectors = {}
    # word_re = None
    # comment_re = r'\s*#'
    check_version = True

    # Used to store TemporaryDirectory instances.
    # Each view gets its own linter instance, apparently.
    _tmp_dir = None

    def cmd(self):
        """Return a list with the command line to execute."""

        cmd = [
            'mypy',
            '*',
            '--follow-imports=silent',  # or 'skip'
            '--ignore-missing-imports',
            '--show-column-numbers',
            '--hide-error-context',
            '@'
        ]

        if self.tempfile_suffix == "-":
            # --shadow-file SOURCE_FILE SHADOW_FILE
            #
            # '@' needs to be the shadow file,
            # while we request the normal filename
            # to be checked in its normal environment.
            # Trying to be smart about view.is_dirty and optimizing '--shadow-file' away
            # doesn't work well with SublimeLinter internals.
            cmd[-1:] = ['--shadow-file', self.filename, '@', self.filename]

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

    def get_chdir(self, settings):
        """Find the chdir to use with the linter."""
        # As explained in https://github.com/python/mypy/issues/2974,
        # we need to overwrite the current working directory
        # for the executed subprocess
        # if the file uses relative imports.
        #
        # Users could set the `chdir` linter setting,
        # but they'd have to do it for *every* file using relative imports,
        # so we just do it for them here if they didn't.
        chdir = settings.get('chdir', None)

        if chdir and os.path.isdir(chdir):
            persist.debug('chdir has been set to: {0}'.format(chdir))
            return chdir
        else:
            if self.filename:
                # Only difference from Linter.get_chdir
                chdir = _find_first_nonpackage_parent(self.filename)
                if chdir != os.path.dirname(self.filename):
                    persist.debug('chdir has been set to: {0}'.format(chdir))
                return chdir
                # return os.path.dirname(self.filename)
            else:
                return os.path.realpath('.')


def _find_first_nonpackage_parent(file_path):
    dir_path = os.path.dirname(file_path)
    while os.path.isfile(os.path.join(dir_path, "__init__.py")):
        parent_path = os.path.dirname(dir_path)
        if parent_path == dir_path:  # Reached file system root; prevent infinite loop
            break
        dir_path = parent_path
    return dir_path


def _onerror(function, path, excinfo):
    persist.printf("mypy: Unable to delete '{}' while cleaning up temporary directory"
                   .format(path))
    import traceback
    traceback.print_exc(*excinfo)


def _cleanup_tmpdirs():
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
