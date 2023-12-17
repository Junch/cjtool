import unittest
import subprocess
import time
import pykd
from cjtool.search import *


class search_test(unittest.TestCase):

    def setUp(self) -> None:
        self.proc = subprocess.Popen(
            './test_projects/_build-x64/Release/observer.exe',
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        attach_process('observer.exe')

    def tearDown(self) -> None:
        pykd.detachProcess()
        self.proc.communicate(input='a'.encode('utf-8'))
        self.proc.stdin.close()
        time.sleep(0.1)
        self.proc.terminate()
        return super().tearDown()

    def test_search(self):
        # 进程还没有销毁掉
        ret = self.proc.poll()
        self.assertIsNone(ret)

        time.sleep(0.1)
        arr = EntitySearcher('observer!ConcreteObserver').search()
        self.assertEqual(len(arr), 2)
