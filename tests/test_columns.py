import importlib
import unittest

import sublime
from SublimeLinter.lint.linter import VirtualView


Linter = importlib.import_module('SublimeLinter-mypy.linter').Mypy


class TestColumns(unittest.TestCase):
    def test_ast_columns_are_utf8_bytes(self):
        self.assertMatch('a.py:1:15: error: Name "missing_name" is not defined  [name-defined]',
                         's = "é😀"; missing_name\n', 10, 'missing_name')

    def test_syntax_columns_are_codepoints_with_a_separate_base_correction(self):
        # mypy 2.3.1 passes SyntaxError.offset directly to its zero-based reporter.
        self.assertMatch('a.py:1:12:1:12: error: Invalid syntax  [syntax]',
                         's = "é😀"; if True: pass\n', 10, 'i')

    def test_ascii_ast_columns_are_unchanged(self):
        self.assertMatch('a.py:1:1: error: Name "missing_name" is not defined  [name-defined]',
                         'missing_name\n', 0, 'missing_name')

    def test_type_ignore_repositioning_is_preserved(self):
        source = 's = "é😀"  # type: ignore[name-defined]\n'
        output = 'a.py:1:1: error: Unused "type: ignore[name-defined]" comment  [unused-ignore]'
        self.assertMatch(output, source, source.index('name-defined'), 'name-defined')

    def assertMatch(self, output, source, col, text):
        linter = Linter(sublime.View(0), {})
        match, = linter.find_errors(output)
        match['filename'] = None
        before = dict(match)
        error = linter.process_match(match, VirtualView(source))
        self.assertIsNotNone(error)
        self.assertEqual(match, before)
        self.assertEqual({k: error[k] for k in ('line', 'start', 'region', 'offending_text')}, {
            'line': 0, 'start': col, 'region': sublime.Region(col, col + len(text)),
            'offending_text': text,
        })
