import unittest
import subprocess
from cjtool.search import *


class search_test(unittest.TestCase):

    def setUp(self) -> None:
        self.proc = subprocess.Popen(
            './test_projects/_build-x64/Release/observer.exe')
        attach_process('observer.exe')

    def tearDown(self) -> None:
        self.proc.kill()
        return super().tearDown()

    def test_search(self):
        # 进程还没有销毁掉
        ret = self.proc.poll()
        self.assertIsNone(ret)

        arr = EntitySearcher('observer!ConcreteObserver').search()
        self.assertEqual(len(arr), 2)
