import unittest
from bmtool import *
import sys

class BmStringRepTest(unittest.TestCase):

    def setUp(self):
        self.tool = StringRep()

    def test_ignore_include_line(self):
        line = '#include "BmRebarSettingImporter.h"'
        newline = self.tool.parse(line)
        self.assertEqual(line, newline)

    def test_ignore_dbg_warn_line(self):
        line = '    DBG_WARN_AND_RETURN_VOID_UNLESS(pDoc, L"pDoc为空!", L"sheny-e", L"2022/03/21");'
        newline = self.tool.parse(line)
        self.assertEqual(line, newline)

    def test_ignore_commented_line(self):
        line = '// std::wstring name = "Tom";'
        newline = self.tool.parse(line)
        self.assertEqual(line, newline)
        self.assertEqual(0, len(self.tool.words))

    def test_ignore_sentence_line(self):
        line = 'std::wstring name = "Tom jumps");'
        newline = self.tool.parse(line)
        self.assertEqual(line, newline)
        self.assertEqual(0, len(self.tool.words))

    def test_ignore_special_character_line(self):
        line = 'std::wstring name = "Tom*");'
        newline = self.tool.parse(line)
        self.assertEqual(line, newline)
        self.assertEqual(0, len(self.tool.words))

    def test_one_pair_quotation (self):
        line = 'std::wstring name = "Tom";'
        new_line = self.tool.parse(line)
        self.assertEqual(new_line, 'std::wstring name = pfnTom;')
        self.assertIn('Tom', self.tool.words)

    def test_two_pairs_quation(self):
        line = 'map["name"] = "Tom";'
        new_line = self.tool.parse(line)
        self.assertEqual(new_line, 'map[pfnName] = pfnTom;')
        self.assertIn('Tom', self.tool.words)
        self.assertIn('name', self.tool.words)

    def test_two_pairs_quation_2(self):
        line = 'map["name"] = "Tom Clause";'
        new_line = self.tool.parse(line)
        self.assertEqual(new_line, 'map[pfnName] = "Tom Clause";')
        self.assertIn('name', self.tool.words)