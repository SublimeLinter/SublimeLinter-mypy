# flake8: noqa
import unittest
import re
import importlib

# Damn you dash separated module names!!!
LinterModule = importlib.import_module('SublimeLinter-contrib-mypy.linter')
Linter = LinterModule.Mypy
regex = Linter.regex


class TestRegex(unittest.TestCase):

    def assertMatch(self, string, expected):
        match = re.match(regex, string)
        self.assertIsNotNone(match)
        self.assertEqual(match.groupdict(), expected)

    def test_regex(self):

        self.assertMatch(
            '/path/to/package/module.py:18:4: error: No return value expected',
            {
                'error': 'error',
                'line': '18',
                'col': '4',
                'warning': None,
                'message': 'No return value expected'
            }
        )

        self.assertMatch(
            '/path/to/package/module.py:40: error: "dict" is not subscriptable, use "typing.Dict" instead',
            {
                'error': 'error',
                'line': '40',
                'col': None,
                'warning': None,
                'message': '"dict" is not subscriptable, use "typing.Dict" instead'
            }
        )

        self.assertMatch(
            '/tmp/yoeai32h2:6:0: error: Cannot find module named \'PackageName.lib\'',
            {
                'error': 'error',
                'line': '6',
                'col': '0',
                'warning': None,
                'message': 'Cannot find module named \'PackageName.lib\''
            }
        )
