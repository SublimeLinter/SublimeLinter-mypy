# flake8: noqa
import unittest
import re
import importlib

import sublime

LinterModule = importlib.import_module('SublimeLinter-mypy.linter')
Linter = LinterModule.Mypy


class TestRegex(unittest.TestCase):
    def assertMatch(self, string, expected):
        linter = Linter(sublime.View(0), {})
        actual = list(linter.find_errors(string))[0]
        # `find_errors` fills out more information we don't want to write down
        # in the examples
        self.assertEqual({k: actual[k] for k in expected.keys()}, expected)

    def assertNoMatch(self, string):
        linter = Linter(sublime.View(0), {})
        actual = list(linter.find_errors(string))
        self.assertFalse(actual)

    def test_no_matches(self):
        self.assertNoMatch('')
        self.assertNoMatch('foo')

    def test_matches(self):
        self.assertMatch(
            '/path/to/package/module.py:18:4: error: No return value expected', {
                'error_type': 'error',
                'line': 17,
                'col': 3,
                'message': 'No return value expected'})

        self.assertMatch(
            '/path/to/package/module.py:40: error: "dict" is not subscriptable, use "typing.Dict" instead', {
                'error_type': 'error',
                'line': 39,
                'col': None,
                'message': '"dict" is not subscriptable, use "typing.Dict" instead'})

        self.assertMatch(
            'codespell_lib\\tests\\test_basic.py:518:5:518:13: error: Module has no attribute "mkfifo"  [attr-defined]', {
                'line': 517,
                'col': 4,
                'end_line': 517,
                'end_col': 12,
            })

        self.assertMatch(
            'codespell_lib\\tests\\test_basic.py:-1:-1:-1:-1: error: Module has no attribute "mkfifo"  [attr-defined]', {
                'line': 0,
                'col': None,
                'end_line': None,
                'end_col': None,
            })

    def test_tmp_files_that_have_no_file_extension(self):
        self.assertMatch(
            '/tmp/yoeai32h2:6:1: error: Cannot find module named \'PackageName.lib\'', {
                'error_type': 'error',
                'line': 5,
                'col': 0,
                'message': 'Cannot find module named \'PackageName.lib\''})
