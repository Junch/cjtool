import unittest
from cjtool.stringtool import StringRep
from colorama import Fore


class StringRep_parse_test(unittest.TestCase):

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
        line = '// std::string name = "Tom";'
        newline = self.tool.parse(line)
        self.assertEqual(line, newline)
        self.assertEqual(0, len(self.tool.words))

    def test_ignore_quotation_started_line(self):
        line = '  "Tom"'
        newline = self.tool.parse(line)
        self.assertEqual(line, newline)
        self.assertEqual(0, len(self.tool.words))

    def test_ignore_sentence_line(self):
        line = 'std::string name = "Tom jumps");'
        newline = self.tool.parse(line)
        self.assertEqual(line, newline)
        self.assertEqual(0, len(self.tool.words))

    def test_ignore_special_character_line(self):
        line = 'std::string name = "Tom*");'
        newline = self.tool.parse(line)
        self.assertEqual(line, newline)
        self.assertEqual(0, len(self.tool.words))

    def test_ignore_assign_line(self):
        line = 'static constexpr wchar_t* pbarNum = L"barNum";'
        newline = self.tool.parse(line)
        self.assertEqual(line, newline)
        self.assertEqual(0, len(self.tool.words))

        line = 'static const char * pbarNum = L"barNum";'
        newline = self.tool.parse(line)
        self.assertEqual(line, newline)
        self.assertEqual(0, len(self.tool.words))

    def test_one_pair_quotation(self):
        line = 'std::string name = "Tom";'
        new_line = self.tool.parse(line)
        self.assertEqual(new_line, 'std::string name = pStrTom;')
        self.assertIn('Tom', self.tool.words)

    def test_wide_character(self):
        line = 'std::wstring name = L"Tom";'
        new_line = self.tool.parse(line)
        self.assertEqual(new_line, 'std::wstring name = pStrTom;')
        self.assertIn('Tom', self.tool.wide_words)

    def test_two_pairs_quation(self):
        line = 'map["name"] = "Tom";'
        new_line = self.tool.parse(line)
        self.assertEqual(new_line, 'map[pStrName] = pStrTom;')
        self.assertIn('Tom', self.tool.words)
        self.assertIn('name', self.tool.words)

    def test_two_pairs_quation_2(self):
        line = 'map["name"] = "Tom Clause";'
        new_line = self.tool.parse(line)
        self.assertEqual(new_line, 'map[pStrName] = "Tom Clause";')
        self.assertIn('name', self.tool.words)

    def test_the_prefix(self):
        line = 'std::string name = "Tom";'
        self.tool.setPrefix('p')
        new_line = self.tool.parse(line)
        self.assertEqual(new_line, 'std::string name = pTom;')
        self.assertIn('Tom', self.tool.words)


class StringRep_get_colored_line_test(unittest.TestCase):

    def setUp(self):
        self.tool = StringRep()

    def test_simple(self):
        line = '  std::string name = "Tom";'
        self.tool.span_buffer = [(21, 26)]
        colored_line = self.tool.get_colored_line(line, 1)
        self.assertEqual(
            colored_line,
            f'{Fore.RED}1{Fore.RESET}:{Fore.RESET}  std::string name = {Fore.GREEN}"Tom"{Fore.RESET};'
        )
