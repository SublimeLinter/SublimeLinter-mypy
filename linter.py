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

from collections import defaultdict
import hashlib
import logging
import os
import shutil
import tempfile
import time
import threading
import getpass

from SublimeLinter.lint import LintMatch, PythonLinter
from SublimeLinter.lint.linter import PermanentError


MYPY = False
if MYPY:
    from typing import Dict, DefaultDict, Iterator, List, Optional, Protocol

    class TemporaryDirectory(Protocol):
        name = None  # type: str


USER = getpass.getuser()
TMPDIR_PREFIX = "SublimeLinter-contrib-mypy-%s" % USER

logger = logging.getLogger("SublimeLinter.plugin.mypy")

# Mapping for our created temporary directories.
# For smarter caching purposes,
# we index different cache folders based on the working dir.
try:
    tmpdirs
except NameError:
    tmpdirs = {}  # type: Dict[str, TemporaryDirectory]
locks = defaultdict(lambda: threading.Lock())  # type: DefaultDict[Optional[str], threading.Lock]


class Mypy(PythonLinter):
    """Provides an interface to mypy."""

    regex = (
        r'^(?P<filename>.+?):'
        r'(?P<line>\d+|-1):((?P<col>\d+|-1):)?'
        r'((?P<end_line>\d+|-1):(?P<end_col>\d+|-1):)?\s*'
        r'(?P<error_type>[^:]+):\s(?P<message>.+?)(\s\s\[(?P<code>.+)\])?$'
    )
    line_col_base = (1, 1)
    tempfile_suffix = 'py'

    # Pretty much all interesting options don't expect a value,
    # so you'll have to specify those in "args" anyway.
    # This dict only contains settings for which we have special handling.
    defaults = {
        'selector': "source.python",
        # Will default to tempfile.TemporaryDirectory if empty.
        "--cache-dir": "",
        "--show-error-codes": True,
        # Need this to silent lints for other files. Alternatively: 'skip'
        "--follow-imports": "silent",
    }

    def cmd(self):
        """Return a list with the command line to execute."""
        cmd = [
            'mypy',
            '${args}',
            '--no-pretty',
            '--show-column-numbers',
            '--hide-error-context',
            '--no-error-summary',
        ]
        if self.filename:
            cmd.extend([
                # --shadow-file SOURCE_FILE SHADOW_FILE
                #
                # '@' needs to be the (temporary) shadow file,
                # while we request the normal filename
                # to be checked in its normal environment.
                '--shadow-file', '${file}', '${temp_file}',
                # The file we want to lint on the surface
                '${file}',
            ])
        else:
            cmd.append('${temp_file}')

        # Compare against `''` so the user can set just `False`,
        # for example if the cache is configured in "mypy.ini".
        if self.settings.get('cache-dir') == '':
            cwd = self.get_working_dir()
            if not cwd:  # abort silently
                self.notify_unassign()
                raise PermanentError()

            if os.path.exists(os.path.join(cwd, '.mypy_cache')):
                self.settings.set('cache-dir', False)  # do not set it as arg
            else:
                # Add a temporary cache dir to the command if none was specified.
                # Helps keep the environment clean by not littering everything
                # with `.mypy_cache` folders.
                try:
                    cache_dir = tmpdirs[cwd].name
                except KeyError:
                    tmpdirs[cwd] = tmp_dir = _get_tmpdir(cwd)
                    cache_dir = tmp_dir.name

                self.settings.set('cache-dir', cache_dir)

        return cmd

    def run(self, cmd, code):
        with locks[self.get_working_dir()]:
            return super().run(cmd, code)

    def find_errors(self, output):
        # type: (str) -> Iterator[LintMatch]
        errors = []  # type: List[LintMatch]
        for error in super().find_errors(output):
            # `"x" defined here` notes are unsorted and not helpful
            # See: https://github.com/python/mypy/issues/10480
            # Introduced: https://github.com/python/mypy/pull/926
            if error.message.endswith(' defined here'):
                continue

            if error.error_type == 'note':
                try:
                    previous = errors[-1]
                except IndexError:
                    pass
                else:
                    if previous.line == error.line and previous.col == error.col:
                        previous['message'] += '\n{}'.format(error.message)
                        continue

            # mypy might report `-1` for unknown values.
            # Only `line` is mandatory within SublimeLinter
            if error.match.group('line') == "-1":  # type: ignore[attr-defined]
                error['line'] = 0
            for group in ('col', 'end_line', 'end_col'):
                if error.match.group(group) == "-1":  # type: ignore[attr-defined]
                    error[group] = None

            errors.append(error)
        yield from errors


class FakeTemporaryDirectory:
    def __init__(self, name):
        # type: (str) -> None
        self.name = name


def _get_tmpdir(folder):
    # type: (str) -> TemporaryDirectory
    folder_hash = hashlib.sha256(folder.encode('utf-8')).hexdigest()[:7]
    tmpdir = tempfile.gettempdir()
    for dirname in os.listdir(tmpdir):
        if dirname.startswith(TMPDIR_PREFIX) and dirname.endswith(folder_hash):
            path = os.path.join(tmpdir, dirname)
            tmp_dir = FakeTemporaryDirectory(path)  # type: TemporaryDirectory
            try:  # touch it so `_cleanup_tmpdirs` doesn't catch it
                os.utime(path)
            except OSError:
                pass
            logger.info("Reuse temporary cache dir at: %s", path)
            return tmp_dir
    else:
        tmp_dir = tempfile.TemporaryDirectory(prefix=TMPDIR_PREFIX, suffix=folder_hash)
        logger.info("Created temporary cache dir at: %s", tmp_dir.name)
        return tmp_dir


def _cleanup_tmpdirs(keep_recent=False):

    def _onerror(function, path, exc_info):
        logger.exception("Unable to delete '%s' while cleaning up temporary directory", path,
                         exc_info=exc_info)

    tmpdir = tempfile.gettempdir()
    for dirname in os.listdir(tmpdir):
        if dirname.startswith(TMPDIR_PREFIX):
            full_path = os.path.join(tmpdir, dirname)
            if keep_recent:
                try:
                    atime = os.stat(full_path).st_atime
                except OSError:
                    pass
                else:
                    if (time.time() - atime) / 60 / 60 / 24 < 14:
                        continue

            shutil.rmtree(full_path, onerror=_onerror)


def plugin_loaded():
    """Attempt to clean up temporary directories from previous runs."""
    _cleanup_tmpdirs(keep_recent=True)


def plugin_unloaded():
    try:
        from package_control import events

        if events.remove('SublimeLinter-mypy'):
            logger.info("Cleanup temporary directories.")
            _cleanup_tmpdirs()

    except ImportError:
        pass
