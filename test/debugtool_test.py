import unittest
import subprocess
from cjtool.debugtool import execute_command
from cjtool.debugtool import match_the_deadly_pattern


class execute_ommand_test(unittest.TestCase):

    def setUp(self) -> None:
        self.proc = subprocess.Popen('notepad.exe')

    def tearDown(self) -> None:
        self.proc.kill()
        return super().tearDown()

    def test_kcn_command(self):
        self.assertTrue(execute_command('notepad.exe', 'kcn'))

    def test_uf_command(self):
        self.assertTrue(
            execute_command(
                'notepad.exe',
                'uf notepad!RestartHandler::ShouldSupportRestartManager'))

    def test_aaaaa_command(self):
        self.assertTrue(execute_command('notepad.exe', 'aaaaa'))

    def test_x_command(self):
        self.assertTrue(
            execute_command('notepad.exe', 'x notepad!RestartHandler::*'))


class match_the_deadly_pattern_test(unittest.TestCase):

    def test_simple(self):
        self.assertTrue(match_the_deadly_pattern('00000000`0000bcde', 'abcde'))
        self.assertTrue(
            match_the_deadly_pattern('0000000a`aaaaaaaa', 'aaaaaaaaaa'))
        self.assertTrue(match_the_deadly_pattern('00000000`0000aaaa', 'baaaa'))

        # 必须可以转成整数才match
        self.assertFalse(match_the_deadly_pattern('00000000`0000aaaa',
                                                  'qaaaa'))
        self.assertFalse(match_the_deadly_pattern('00000000`0000bcde', 'bcde'))
        self.assertFalse(match_the_deadly_pattern('00000000`a0000aaa',
                                                  'aaaaa'))
