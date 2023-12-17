import unittest
import subprocess
from cjtool.cdbtool import execute_command


class TestCdbTool(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.proc = subprocess.Popen('notepad.exe')

    @classmethod
    def tearDownClass(cls) -> None:
        cls.proc.kill()
        cls.proc.wait()

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
