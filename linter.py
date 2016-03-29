#
# linter.py
# Linter for SublimeLinter3, a code checking framework for Sublime Text 3
#
# Written by Fred Callaway
# Copyright (c) 2015 Fred Callaway
#
# License: MIT
#

"""This module exports the Mypy plugin class."""

from SublimeLinter.lint import PythonLinter, util, highlight


class Mypy(PythonLinter):
    """Provides an interface to mypy."""

    syntax = 'python'
    cmd = 'mypy * @'
    version_args = '--version'
    version_re = r'(?P<version>\d+\.\d+\.\d+)'
    version_requirement = '>= 0.2'
    regex = r'^.+\.py:(?P<line>\d+): error: (?P<message>.+)'
    multiline = False
    line_col_base = (1, 1)
    tempfile_suffix = None
    error_stream = util.STREAM_BOTH
    selectors = {}
    word_re = None
    defaults = {}
    default_type = highlight.WARNING
    inline_settings = None
    inline_overrides = None
    comment_re = None
    check_version = False
