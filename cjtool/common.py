#!/usr/bin/python
# coding:utf-8
import pykd
import sys
import re
import stl
from datetime import datetime
from threading import Thread
import weakref
from enum import Enum
import time
import json
from json import JSONEncoder
from sourceline import Inspect
import atexit

# https://stackoverflow.com/questions/37340049/how-do-i-print-colored-output-to-the-terminal-in-python/37340245


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_warning(msg):
    print("{0}WARNING: {2}{1}".format(bcolors.WARNING, bcolors.ENDC, msg))


def getProcessByName(name):
    processid = 0
    lower_name = name.lower()
    for (pid, pname, user) in pykd.getLocalProcesses():
        if pname.lower() == lower_name:
            processid = pid
            break
    return processid


class BaseType:
    def __init__(self, typename):
        self.typename = typename
        self.vftables = []
        self.vftable_methods = []
        self.vftable_offsets = []

    @property
    def size(self):
        return pykd.typeInfo(self.typename).size()

    def get_vftables(self):
        if self.vftables:
            return self.vftables

        (moduleName, methodName) = self.typename.split('!')
        mod = pykd.module(moduleName)
        symbol = "{}::`vftable'".format(methodName)
        for (name, address) in mod.enumSymbols(symbol):
            self.vftables.append(address)
        self.vftables.sort()
        return self.vftables

    def print_vftables(self):
        vftables = self.get_vftables()

        def link(addr):
            return "<link cmd=\"ln 0x{0:x}\">{0:x}</link>".format(addr)

        pykd.dprintln(
            "vftable: [{}]".format(', '.join(link(x) for x in vftables)), True)

    def get_vftable_methods(self):
        if self.vftable_methods:
            return self.vftable_methods

        vftables = self.get_vftables()
        nCount = len(vftables)
        for index, addr in enumerate(vftables):
            # print("{:08x} ######## ######## {}".format(addr, index))
            self.vftable_methods.append([])
            while True:
                func_addr = pykd.loadDWords(addr, 1)[0]
                symbol = pykd.findSymbol(func_addr)
                if symbol == "{:x}".format(func_addr):
                    break

                self.vftable_methods[index].append((addr, func_addr, symbol))
                # print("{:08x} {:08x} {}".format(addr, func_addr, symbol))
                addr = addr + 4
                if (index + 1 < nCount and addr >= vftables[index + 1]):
                    break
        return self.vftable_methods

    def print_vftable_methods(self):
        vftable_methods = self.get_vftable_methods()
        for index, methods in enumerate(vftable_methods):
            print("######## ######## {}".format(index))
            for method in methods:
                print("{:08x} {:08x} {}".format(method[0], method[1],
                                                method[2]))

    def get_vftable_offsets(self, addr):
        if self.vftable_offsets:
            return self.vftable_offsets

        vftables = self.get_vftables()
        offsets = []
        for vtab in vftables:
            cmd = "s -[w]d {:x} L?0x7fffffff {:x}".format(addr, vtab)
            if pykd.is64bitSystem():
                cmd = "s -[w]q {:x} L?0x7fffffffffffffff {:x}".format(
                    addr, vtab)

            result = pykd.dbgCommand(cmd)
            lines = result.split('\n')
            vftable_addr = 0
            for line in lines:
                if (line == ''):
                    continue
                elif (".natvis" in line):
                    continue

                loc = line.split()[0]
                if pykd.is64bitSystem():
                    loc = loc.replace('`', '')
                vftable_addr = int(loc, 16)
                break

            offsets.append(vftable_addr)

        self.vftable_offsets = [x - offsets[0] for x in offsets]
        return self.vftable_offsets

    def get_this_offset(self, addr, method_name):
        vftable_methods = self.get_vftable_methods()
        found = False
        for index, methods in enumerate(vftable_methods):
            for method in methods:
                if method_name == method[2]:
                    found = True
                    break

            if found:
                break

        if not found:
            return 0

        vftable_offsets = self.get_vftable_offsets(addr)
        return vftable_offsets[index]

    def get_entities(self):
        # https://docs.microsoft.com/en-us/windows-hardware/drivers/gettingstarted/virtual-address-spaces
        vftables = self.get_vftables()
        cmd = "s -[w]d 0x0 L?0x7fffffff {:x}".format(vftables[0])
        if pykd.is64bitSystem():
            cmd = "s -[w]q 0x0 L?0x7fffffffffffffff {:x}".format(vftables[0])

        result = pykd.dbgCommand(cmd)
        if not result:
            return []

        lines = result.split('\n')
        entities = []
        for line in lines:
            if (line == ''):
                continue
            elif (".natvis" in line):
                continue

            loc = line.split()[0]
            if pykd.is64bitSystem():
                loc = loc.replace('`', '')

            entities.append(int(loc, 16))
        entities.sort()
        return entities


def getEntities(fullName):
    baseType = BaseType(fullName)
    return baseType.get_entities()


def get_return_addrss(localAddr):
    disas = pykd.dbgCommand("uf {:x}".format(localAddr)).split('\n')
    for line in disas:
        match = re.search(r"(.*)\s+ret\b", line)
        if match:
            columns = match.group(1)
            addr = columns.split()[-2]
            if pykd.is64bitSystem():
                addr = addr.replace('`', '')
            return int(addr, 16)
    return 0


def dvalloc(size):
    line = pykd.dbgCommand(".dvalloc {}".format(size))
    match = re.search(r"Allocated (.*) bytes starting at (.*)", line)
    if match:
        size = match.group(1)
        addr = match.group(2)
        if pykd.is64bitSystem():
            addr = addr.replace('`', '')
        return (int(size), int(addr, 16))


def dvfree(size, addr):
    pykd.dbgCommand(".dvfree {} {:#x}".format(size, addr))


def mallocVar():
    # get a malloc function. May be we have not its prototype in pdb file,
    # so we need to define prototype manually
    PVoid = pykd.typeInfo("Void*")
    size_t = pykd.typeInfo("Int8B") if pykd.getCPUMode(
    ) == pykd.CPUType.AMD64 else pykd.typeInfo("Int4B")
    mallocProto = pykd.defineFunction(PVoid, pykd.callingConvention.NearC)
    mallocProto.append("size", size_t)
    malloc = pykd.typedVar(
        mallocProto,
        pykd.getOffset("malloc"))  # getOffset("malloc") may take a long time
    return malloc


def malloc_string(sz):
    malloc = mallocVar()
    length = 24
    if pykd.is64bitSystem():
        length = 32  # 0x20
    strlen = len(sz)
    if (strlen >= 0x10):
        length = strlen + 1 + length
    addr = malloc(length)
    stl.string.write(addr, sz)
    stringVar = pykd.typedVar(
        "std::basic_string<char,std::char_traits<char>,std::allocator<char> >",
        addr)
    return stringVar


def malloc_wstring(sz):
    malloc = mallocVar()
    length = 24
    if pykd.is64bitSystem():
        length = 32  # 0x20
    strlen = len(sz)
    if (strlen >= 0x8):
        length = (strlen + 1) * 2 + length
    addr = malloc(length)
    stl.wstring.write(addr, sz)
    stringVar = pykd.typedVar(
        "std::basic_string<wchar_t,std::char_traits<wchar_t>,"
        "std::allocator<wchar_t> >", addr)
    return stringVar


def free_string(stringVar):
    free = freeVar()
    free(stringVar.getAddress())


def freeVar():
    # get a malloc function. May be we have not its prototype in pdb file,
    # so we need to define prototype manually
    # Void = pykd.typeInfo("Void")
    # PVoid = pykd.typeInfo("Void*")
    freeProto = pykd.defineFunction(
        pykd.baseTypes.VoidPtr, pykd.callingConvention.NearC)
    freeProto.append("ptr", pykd.baseTypes.VoidPtr)
    free = pykd.typedVar(
        freeProto,
        pykd.getOffset("free"))  # getOffset("malloc") may take a long time
    return free


def allocConsole():
    # https://stackoverflow.com/questions/30098229/win32-application-write-output-to-console-using-printf
    # The same as calling the following APIs
    # FreeConsole();
    # AllocConsole();
    # freopen("CON", "w", stdout);
    Bool = pykd.typeInfo("Bool")
    FreeConsole_Type = pykd.defineFunction(
        Bool, pykd.callingConvention.NearStd)
    FreeConsole = pykd.typedVar(
        FreeConsole_Type, pykd.getOffset("KERNELBASE!FreeConsole"))
    FreeConsole()

    AllocConsole_Type = pykd.defineFunction(
        Bool, pykd.callingConvention.NearStd)
    AllocConsole = pykd.typedVar(
        AllocConsole_Type, pykd.getOffset("KERNELBASE!AllocConsole"))
    AllocConsole()

    # Get stdout
    acrt_iob_func_Type = pykd.defineFunction(
        pykd.baseTypes.VoidPtr, pykd.callingConvention.NearStd)
    acrt_iob_func_Type.append("nStdHandle", pykd.baseTypes.UInt4B)
    acrt_iob_func = pykd.typedVar(
        acrt_iob_func_Type, pykd.getOffset("ucrtbase!__acrt_iob_func"))
    stdout = acrt_iob_func(1)

    freopen_Type = pykd.defineFunction(
        pykd.baseTypes.VoidPtr, pykd.callingConvention.NearStd)
    freopen_Type.append("filename", pykd.baseTypes.VoidPtr)
    freopen_Type.append("mode", pykd.baseTypes.VoidPtr)
    freopen_Type.append("stream ", pykd.baseTypes.VoidPtr)
    freopen = pykd.typedVar(freopen_Type, pykd.getOffset("ucrtbase!freopen"))
    param = pykd.stackAlloc(100)
    pykd.writeCStr(param, "CON")
    pykd.writeCStr(param + 8, "w")
    freopen(param, param + 8, stdout)
    pykd.stackFree(100)


def natvis(moduleName, var, depth=1):
    # Need copy the stl.natvis to the site-packages\pykd\Visualizers
    typename = var.type().name()
    addr = var.getAddress()
    desc = pykd.dbgCommand("dx -r{} (*(({}!{} *){:#x}))".format(
        depth, moduleName, typename, addr))
    return desc


def injectDll(dllpath):
    (size, addr) = dvalloc(len(dllpath))
    stl.string.write(addr, dllpath)

    # PVoid = pykd.typeInfo("Void*")
    loadProto = pykd.defineFunction(PVoid, pykd.callingConvention.NearStd)
    loadProto.append("ptr", PVoid)
    load = pykd.typedVar(loadProto, pykd.getOffset("KERNELBASE!LoadLibraryA"))
    handle = load(addr)

    dvfree(size, addr)
    return handle


def ejectDll(handle):
    Bool = pykd.typeInfo("Bool")
    PVoid = pykd.typeInfo("Void*")
    freeProto = pykd.defineFunction(Bool, pykd.callingConvention.NearStd)
    freeProto.append("ptr", PVoid)
    free = pykd.typedVar(freeProto, pykd.getOffset("KERNELBASE!FreeLibrary"))
    ret = free(handle)
    return ret


def castAddress(addr):
    vptr = pykd.loadDWords(addr, 1)[0]
    # Demo: ContactService!csf::person::spark::SparkPersonRecord::`vftable'
    symbol_name = pykd.findSymbol(vptr)
    match = re.search(r"(.*)::`vftable'", symbol_name)
    typename = ""
    if match:
        typename = match.group(1)
    return pykd.typedVar(typename, addr)


def castTypedVar(var):
    addr = var.getAddress()
    return castAddress(addr)


class BreakPointType(Enum):
    Normal = 0
    OneShot = 1


class FunctionData:
    def __init__(self) -> None:
        self.funtionName = ''      # 函数名
        self.fileName = ''         # 文件名
        self.startLineNumber = 0   # 函数开始行
        self.endLineNumber = 0     # 函数结束行


class BreakPointHit:
    def __init__(self) -> None:
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


class BreakPointManager(object):
    def __init__(self, pid, logfilepath) -> None:
        super(BreakPointManager, self).__init__()
        # https://blog.csdn.net/nankai0912678/article/details/105269848
        atexit.register(self.cleanup)
        self.breakpoints = []
        self.pid = pid
        self.breakpointHits = []
        self.logfilepath = logfilepath

    def cleanup(self):
        functionHits = {}
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
        with open(self.logfilepath, 'w', encoding='utf-8') as json_file:
            json.dump(o, json_file, indent=4)

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
                hit.offset = self.start.offset
                hit.retOffset = self.start.retOffset
                hit.funtionName = self.start.symbol
                hit.isStart = False
                hit.threadId = pykd.getThreadSystemID()
                self.start.manager.writeLog(hit)

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
                hit.offset = self.offset
                hit.retOffset = self.retOffset
                hit.funtionName = self.symbol
                hit.isStart = True
                hit.appendix = appendix
                hit.threadId = pykd.getThreadSystemID()
                self.manager.writeLog(hit)
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


gDebugLoop = True


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
                sys.stdout.write(f"Starting process: {self.path} ")
                spinner.start()
                pykd.startProcess(self.path)
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
            if attached and self.pid != 0:
                pykd.detachProcess()
