import pykd
from datetime import datetime
from threading import Thread
import weakref
from enum import Enum
import time
import json
#from json import JSONEncoder
from sourceline import Inspect
import atexit
import linecache
import zipfile
from pathlib import Path
import tempfile
import re
import sys
import psutil
from common import print_warning, get_return_addrss

gDebugLoop = True

class BreakPointType(Enum):
    Normal = 0
    OneShot = 1


class FunctionData:
    def __init__(self) -> None:
        self.funtionName = ''      # 函数名
        self.fileName = ''         # 文件名
        self.startLineNumber = 0   # 函数开始行
        self.endLineNumber = 0     # 函数结束行
        self.comment = ''          # 代码点评

    def content(self) -> str:
        # 确定函数名所在的行
        functionName = self.funtionName.split('!')[1]  # 去掉!前的模块名称
        # 可能带namespace，而namespace很可能不包含在函数名所在的
        functionName = functionName.split('::')[-1] + '('

        if not self.fileName:
            return f"没有找到文件路径"

        if not Path(self.fileName).exists():
            return f"没有找到文件 {self.fileName}"

        nCount = 20
        for i in range(self.startLineNumber, 0, -1):
            line = linecache.getline(self.fileName, i)
            nCount = nCount - 1
            if functionName in line or nCount == 0:  # 最多往上搜索20行
                break

        lines = []
        for i in range(i, self.endLineNumber + 1):
            line = linecache.getline(self.fileName, i)
            lines.append(line)

        return ''.join(lines)

    def assign(self, o: dict) -> None:
        self.__dict__ = o

    def __repr__(self):
        return f"<FunctionData: {self.funtionName}: {self.fileName} ({self.startLineNumber} - {self.endLineNumber})>"


class BreakPointHit:
    def __init__(self) -> None:
        self.id = 0                # id号
        self.offset = 0            # 函数入口偏移量
        self.retOffset = 0         # 函数出口偏移量
        self.funtionName = ''      # 函数名
        self.isStart = True        # 函数入口或出口
        self.appendix = ''         # 附件信息
        self.threadId = 0          # 线程Id

    def __repr__(self):
        return f"<common.BreakPointHit offset:{self.offset}, functionName:{self.functionName}, isStart:{self.isStart}>"

    def assign(self, o: dict) -> None:
        self.__dict__ = o

    def pairWith(self, hit) -> bool:
        return self.offset == hit.offset and \
            self.threadId == hit.threadId and \
            self.isStart != hit.isStart


class BreakPointPairError(Exception):
    def __init__(self, hit: BreakPointHit):
        self.message = f"The hit {hit.id} is not matched"
        super().__init__(self.message)


class BreakPointManager(object):
    def __init__(self, pid, logfilepath) -> None:
        super(BreakPointManager, self).__init__()
        # https://blog.csdn.net/nankai0912678/article/details/105269848
        atexit.register(self.cleanup)
        self.breakpoints = []
        self.pid = pid
        self.breakpointHits = []
        self.logfilepath = logfilepath
        self.currentid = 100

    def create_json(self) -> str:
        functionHits = {}
        if not psutil.pid_exists(self.pid):
            print(f"The process {self.pid} has been terminated.")
        else:
            print(f"The process {self.pid} is still running.")
        inspect = Inspect(self.pid)
        for hit in self.breakpointHits:
            offset = hit['offset']
            if offset not in functionHits:
                lineInfo = inspect.GetLineFromAddr64(offset)
                endLineInfo = inspect.GetLineFromAddr64(hit['retOffset'])

                data = FunctionData()
                data.funtionName = hit['funtionName']
                data.fileName = lineInfo.FileName
                data.startLineNumber = lineInfo.LineNumber
                data.endLineNumber = endLineInfo.LineNumber
                functionHits[offset] = data.__dict__

        o = {'hits': self.breakpointHits, 'functions': functionHits}
        with tempfile.NamedTemporaryFile(mode='w+t', delete=False, encoding='utf-8') as json_file:
            json.dump(o, json_file, indent=4)
            return json_file.name

    def create_tree(self) -> str:
        lines = []
        stack = []
        depth = -1

        try:
            for item in self.breakpointHits:
                hit = BreakPointHit()
                hit.assign(item)

                paired = False
                if stack:
                    topItem = stack[-1]
                    if hit.pairWith(topItem):
                        if hit.isStart:
                            raise BreakPointPairError(hit)
                        paired = True

                if paired:
                    stack.pop()
                    depth = depth - 1
                else:
                    if not hit.isStart:
                        raise BreakPointPairError(hit)
                    stack.append(hit)
                    depth = depth + 1
                    lines.append('\t'*depth + f"{hit.id} {hit.funtionName}\n")
        except Exception as errtxt:
            print_warning(errtxt)

        with tempfile.NamedTemporaryFile(mode='w+t', delete=False, encoding='utf-8') as treefile:
            treefile.writelines(lines)
            return treefile.name

    def cleanup(self):
        jsonfname = self.create_json()
        treefname = self.create_tree()

        with zipfile.ZipFile(self.logfilepath, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(jsonfname, arcname='monitor.json')
            zf.write(treefname, arcname='tree.txt')
        print(f'{self.logfilepath} is saved.')

    def writeLog(self, hit: BreakPointHit):
        local_str_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        dir = '>>' if hit.isStart else '<<'
        log = "{} [{:05x}] {}{}{}\n".format(local_str_time,
                                            hit.threadId,
                                            dir,
                                            hit.funtionName,
                                            hit.appendix)
        sys.stdout.write(log)
        self.breakpointHits.append(hit.__dict__)

    def addBreakPoint(self,
                      moduName,
                      funcName,
                      callback=None,
                      bptype=BreakPointType.Normal):
        mod = pykd.module(moduName)
        for (name, offset) in mod.enumSymbols(funcName):
            match = re.search(r".*::`.*'", name)
            if match:
                continue
            self.__addBreakPoint(offset, callback, bptype)

    def removeBreakPoint(self, bp):
        if bp in self.breakpoints:
            self.breakpoints.remove(bp)

    def __addBreakPoint(self, offset, callback, bptype):

        class EndBreakpoint(pykd.breakpoint):
            def __init__(self, offset, bptype, start):
                super(EndBreakpoint, self).__init__(offset)
                self.type = bptype
                # http://blog.soliloquize.org/2016/01/21/Python弱引用的使用与注意事项
                self.start = weakref.proxy(start)

            def onHit(self):
                hit = BreakPointHit()
                hit.id = self.start.manager.currentid
                hit.offset = self.start.offset
                hit.retOffset = self.start.retOffset
                hit.funtionName = self.start.symbol
                hit.isStart = False
                hit.threadId = pykd.getThreadSystemID()
                self.start.manager.writeLog(hit)
                self.start.manager.currentid = self.start.manager.currentid + 1
                if self.type == BreakPointType.OneShot:
                    self.start.remove()
                return False

        class StartBreakpoint(pykd.breakpoint):
            def __init__(self, offset, callback, bptype, manager: BreakPointManager):
                super(StartBreakpoint, self).__init__(offset)
                self.symbol = pykd.findSymbol(offset)
                # For debug
                # print(self.symbol)
                self.offset = offset
                self.callback = callback
                self.type = bptype
                self.retOffset = get_return_addrss(offset)
                self.endBreakPoint = EndBreakpoint(
                    self.retOffset, self.type, self)
                self.manager = weakref.proxy(manager)

            def remove(self):
                self.manager.removeBreakPoint(self)

            def onHit(self):
                appendix = ''
                if self.callback:
                    ret = self.callback(self)
                    if ret:
                        appendix = f" {ret}"

                hit = BreakPointHit()
                hit.id = self.manager.currentid
                hit.offset = self.offset
                hit.retOffset = self.retOffset
                hit.funtionName = self.symbol
                hit.isStart = True
                hit.appendix = appendix
                hit.threadId = pykd.getThreadSystemID()
                self.manager.writeLog(hit)
                self.manager.currentid = self.manager.currentid + 1
                return False

        try:
            bp = StartBreakpoint(offset, callback, bptype, self)
            self.breakpoints.append(bp)
        except Exception as errtxt:
            print_warning(errtxt)


class ExceptionHandler(pykd.eventHandler):
    def __init__(self, debugger):
        super(ExceptionHandler, self).__init__()
        self.debugger = debugger

    def onDebugOutput(self, text, type):
        # sys.stdout.write(text)
        pass

    def onLoadModule(self, base, mod_name):
        self.debugger.addBreakPointsInModule(mod_name)


# https://stackoverflow.com/questions/5174810/how-to-turn-off-blinking-cursor-in-command-window
# https://stackoverflow.com/questions/30126490/how-to-hide-console-cursor-in-c
# https://pythonadventures.wordpress.com/tag/hide-cursor/
def show_cursor(visible=True):
    import ctypes

    class _CursorInfo(ctypes.Structure):
        _fields_ = [("size", ctypes.c_int), ("visible", ctypes.c_byte)]

    STD_OUTPUT_HANDLE = -11
    kernel32 = ctypes.windll.kernel32

    ci = _CursorInfo()
    handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    kernel32.GetConsoleCursorInfo(handle, ctypes.byref(ci))
    ci.visible = visible
    kernel32.SetConsoleCursorInfo(handle, ctypes.byref(ci))


# https://stackoverflow.com/questions/4995733/how-to-create-a-spinning-command-line-cursor
class Spinner:
    busy = False
    delay = 0.2

    @staticmethod
    def spinning_cursor():
        while True:
            for cursor in '|/-\\':
                yield cursor

    def __init__(self, delay=None):
        self.spinner_generator = self.spinning_cursor()
        if delay and float(delay):
            self.delay = delay

    def spinner_task(self):
        show_cursor(False)
        while self.busy:
            sys.stdout.write(next(self.spinner_generator))
            sys.stdout.flush()
            time.sleep(self.delay)
            sys.stdout.write('\b')
            sys.stdout.flush()
        show_cursor()

    def start(self):
        self.busy = True
        Thread(target=self.spinner_task).start()

    def stop(self):
        self.busy = False
        time.sleep(self.delay)


def exit_gracefully(signal, frame):
    global gDebugLoop
    gDebugLoop = False
    pykd.breakin()
    pykd.dprintln("You pressed CTRL+C")


def get_module_names():
    # lines = pykd.dbgCommand("lm1m").split('\n')
    # lines.pop()
    # return lines
    modules = pykd.getModulesList()
    return [x.name() for x in modules]


class BPRecord:
    def __init__(self, moduName, funcName, callback, bptype):
        self.moduName = moduName
        self.funcName = funcName
        self.callback = callback
        self.type = bptype
        self.added = False


class Debugger(Thread):
    def __init__(self, pid=0, exepath=None, logfilepath=None, prelude=None):
        super(Debugger, self).__init__()
        self.pid = pid
        self.path = exepath
        self.breakpoints = []
        self.manager = BreakPointManager(pid, logfilepath)
        self.prelude = prelude

    def setPrelude(self, prelude):
        self.prelude = prelude

    def addBreakPoint(self,
                      symbol,
                      callback=None,
                      bptype=BreakPointType.Normal):
        (moduName, funcName) = symbol.split('!')
        self.breakpoints.append(BPRecord(moduName, funcName, callback, bptype))

    def addBreakPointsInModule(self, mod_name):
        for record in self.breakpoints:
            if record.added:
                continue
            pattern = f"{record.moduName}$"
            matchObj = re.match(pattern, mod_name, re.I)
            if matchObj:
                self.manager.addBreakPoint(mod_name, record.funcName,
                                           record.callback, record.type)
                record.added = True

    def run(self):
        attached = False
        started = False
        try:
            pykd.initialize()
            spinner = Spinner()
            if self.pid != 0:
                msg = f"Attaching to process: pid {self.pid} "
                sys.stdout.write(msg)
                spinner.start()
                pykd.attachProcess(self.pid)
                # End spinning cursor
            elif self.path is not None:
                print(f"Path: {self.path}")
                sys.stdout.write(f"Starting process: {self.path} ")
                spinner.start()
                pykd.startProcess(self.path)
                self.pid = pykd.expr("$tpid")
                self.manager.pid = self.pid
                started = True
            else:
                print("Fail to debug due to invalided pid and path")
                exit()

            attached = True
            pykd.handler = ExceptionHandler(self)

            modules = get_module_names()
            for mod_name in modules:
                self.addBreakPointsInModule(mod_name)
            spinner.stop()
            print(f"\nbreakpoints count: {len(self.manager.breakpoints)}")
            for index, item in enumerate(self.manager.breakpoints):
                print(f"{index}: {item.symbol}")
            print("\nStart monitoring")

            if self.prelude:
                self.prelude()

            while (gDebugLoop):
                pykd.go()
        except Exception as errtxt:
            print(errtxt)
        finally:
            if attached and not started:
                pykd.detachProcess()
