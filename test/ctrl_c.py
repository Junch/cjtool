import ctypes
import sys

kernel = ctypes.windll.kernel32

# pid = int(sys.argv[1])
# kernel.FreeConsole()
# kernel.AttachConsole(pid)
# kernel.SetConsoleCtrlHandler(None, 1)
# kernel.GenerateConsoleCtrlEvent(0, 0)
# sys.exit(0)

pid = int(sys.argv[1])
r = kernel.FreeConsole()
if r == 0: exit(-1)
kernel.AttachConsole(pid)
if r == 0: exit(-1)
kernel.SetConsoleCtrlHandler(None, 1)
if r == 0: exit(-1)
kernel.GenerateConsoleCtrlEvent(0, 0)
sys.exit(0)
