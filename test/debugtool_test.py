import unittest
import subprocess
from cjtool.debugtool import execute_command


class execute_command_test(unittest.TestCase):

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
                'notepad.exe', 'uf notepad!TraceFileSaveStart'))

    def test_aaaaa_command(self):
        self.assertTrue(execute_command('notepad.exe', 'aaaaa'))

    def test_x_command(self):
        self.assertTrue(
            execute_command('notepad.exe', 'x notepad!*Start'))

    def test_aaaaaaaaaaaaaaaaaaaa_command(self):
        self.assertTrue(execute_command('notepad.exe', 'aaaaaaaaaaaaaaaaaaaa'))
