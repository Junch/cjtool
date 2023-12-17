import unittest
import subprocess
import time
import sys
# from pathlib import Path

# https://stackoverflow.com/questions/7085604/sending-c-to-python-subprocess-objects-on-windows
# https://stackoverflow.com/questions/813086/can-i-send-a-ctrl-c-sigint-to-an-application-on-windows/15281070#15281070
# python -m unittest test\monitor_test.py

class monitor_test(unittest.TestCase):

    def setUp(self) -> None:
        self.proc = subprocess.Popen(
            [sys.executable, './cjtool/monitor.py',
                './test_projects/_build-x64/Release/observer.yaml'],
            creationflags=subprocess.CREATE_NEW_CONSOLE)

    def tearDown(self) -> None:
        time.sleep(1)
        self.proc.kill()
        return super().tearDown()

    def test_monitor_result(self):
        # 进程还没有销毁掉
        time.sleep(5)
        ret = self.proc.poll()
        self.assertIsNone(ret)

        subprocess.check_call([
            sys.executable,
            "-c",
            "import ctypes, sys;"
            "kernel = ctypes.windll.kernel32;"
            "pid = int(sys.argv[1]);"
            "kernel.FreeConsole();"
            "kernel.AttachConsole(pid);"
            "kernel.SetConsoleCtrlHandler(None, 1);"
            "kernel.GenerateConsoleCtrlEvent(0, 0);"
            "sys.exit(0)",
            str(self.proc.pid)
        ])  # Send Ctrl-C

        # script_path = Path(__file__).parent.absolute().joinpath('ctrl_c.py')
        # subprocess.check_call([sys.executable, script_path, str(self.proc.pid)]) # Send Ctrl-C
