# flake8: noqa
from __future__ import annotations
import importlib
import inspect
import os
import re
import unittest

import sublime

from SublimeLinter.lint import Linter as BaseLinter


class TestRegexMeta(type):
    """Metaclass that automatically generates test methods from examples."""
    def __new__(mcs, name, bases, attrs):
        if 'Linter' in attrs and isinstance(attrs['Linter'], str):
            attrs['Linter'] = mcs.resolve_linter(attrs['Linter'])

        # Process examples if they exist
        if 'examples' in attrs:
            examples = attrs['examples']

            # If examples is a single (string, dict) tuple, convert it to a list
            if isinstance(examples, tuple) and len(examples) == 2 and isinstance(examples[0], str) and isinstance(examples[1], dict):
                examples = [examples]

            # Create test for matches
            attrs['test_matches'] = mcs.create_matches_test(examples)

        # Process does_not_match if they exist
        if 'does_not_match' in attrs:
            does_not_match = attrs['does_not_match']

            # If does_not_match is a single string, convert it to a list
            if isinstance(does_not_match, str):
                does_not_match = [does_not_match]

            # Create test for no matches
            attrs['test_no_matches'] = mcs.create_no_matches_test(does_not_match)

        return super().__new__(mcs, name, bases, attrs)

    @staticmethod
    def resolve_linter(linter_name):
        """
        Resolve a linter name string to the actual linter class.

        Strategy 0: Resolve the fully qualified path
        Strategy 1: Try standard naming pattern - SublimeLinter-{name}.linter.{Name}
        Strategy 2: Try to infer from test file location
        """
        def import_(module_name, linter_name):
            linter_module = importlib.import_module(module_name)
            return getattr(linter_module, linter_name)

        if "." in linter_name:
            try:
                return import_(*linter_name.rsplit(".", 1))
            except (ImportError, AttributeError):
                pass

        # Try the standard pattern first (Strategy 1)
        for module_name in (
            f"SublimeLinter-{linter_name.lower()}.linter",
            f"SublimeLinter-contrib-{linter_name.lower()}.linter",
        ):
            try:
                return import_(module_name, linter_name)
            except (ImportError, AttributeError):
                pass

        # If that fails, try to infer from the test file location (Strategy 2)
        # Get the caller's frame (stack level 2 to get past resolve_linter and __new__)
        frame = inspect.stack()[2]
        module = inspect.getmodule(frame[0])
        if module and (module_path := module.__file__):
            parts = module_path.split(os.sep)
            for candidate in ("Packages", "InstalledPackages"):
                try:
                    i = parts.index(candidate)
                except ValueError:
                    pass
                else:
                    package_name = parts[i + 1]
                    module_name = f"{package_name}.linter"
                    try:
                        import_(module_name, linter_name)
                    except (ImportError, AttributeError):
                        break

        # If all strategies fail, raise a helpful error
        raise ImportError(
            f"Could not resolve Linter='{linter_name}'. "
            f"Please ensure your package follows the naming convention "
            f"SublimeLinter-<contrib->{linter_name.lower()}, provide a full "
            "importable path or the Linter class."
        )

    @staticmethod
    def create_matches_test(examples):
        """Create a test method for matching examples."""
        def test_matches(self):
            for string, expected in examples:
                with self.subTest(string=string):
                    self.assertMatch(string, expected)
        return test_matches

    @staticmethod
    def create_no_matches_test(does_not_match):
        """Create a test method for non-matching examples."""
        def test_no_matches(self):
            for string in does_not_match:
                with self.subTest(string=string):
                    self.assertNoMatch(string)
        return test_no_matches


class TestRegex(unittest.TestCase, metaclass=TestRegexMeta):
    """
    Base class for testing regular expressions with examples.

    End users just need to define:
    - Linter: the Linter class under test
    - examples: List/tuple of (string, expected_dict) for patterns that should match
    - does_not_match: List/tuple of strings for patterns that shouldn't match

    The test runner automatically generates test methods from these examples.
    """
    Linter: type[BaseLinter] | str

    def assertMatch(self, string, expected):
        """Assert that a string matches an expected pattern."""
        assert isinstance(self.Linter, BaseLinter)
        linter = self.Linter(sublime.View(0), {})
        actual = list(linter.find_errors(string))[0]
        # `find_errors` fills out more information we don't want to write down
        # in the examples
        self.assertEqual({k: actual[k] for k in expected.keys()}, expected)

    def assertNoMatch(self, string):
        """Assert that a string doesn't match any pattern."""
        assert isinstance(self.Linter, BaseLinter)
        linter = self.Linter(sublime.View(0), {})
        actual = list(linter.find_errors(string))
        self.assertFalse(actual)


class TestMyPyRegex(TestRegex):
    Linter = "Mypy"

    examples = [
        ('/path/to/package/module.py:18:4: error: No return value expected', {
            'error_type': 'error',
            'line': 17,
            'col': 3,
            'message': 'No return value expected'
        }),
        ('/path/to/package/module.py:40: error: "dict" is not subscriptable, use "typing.Dict" instead', {
            'error_type': 'error',
            'line': 39,
            'col': None,
            'message': '"dict" is not subscriptable, use "typing.Dict" instead'
        }),
        ('codespell_lib\\tests\\test_basic.py:518:5:518:13: error: Module has no attribute "mkfifo"  [attr-defined]', {
            'line': 517,
            'col': 4,
            'end_line': 517,
            'end_col': 12,
        }),
        ('codespell_lib\\tests\\test_basic.py:-1:-1:-1:-1: error: Module has no attribute "mkfifo"  [attr-defined]', {
            'line': 0,
            'col': None,
            'end_line': None,
            'end_col': None,
        }),
        # check tmp_files that might not have extensions
        ('/tmp/yoeai32h2:6:1: error: Cannot find module named \'PackageName.lib\'', {
            'error_type': 'error',
            'line': 5,
            'col': 0,
            'message': 'Cannot find module named \'PackageName.lib\''
        })
    ]

    does_not_match = [
        '',
        'foo'
    ]
