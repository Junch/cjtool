#!/usr/bin/python
# coding:utf-8
import pykd
import re
import stl

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


# cache
cache_dword_size = None


def get_arch():
    # https://github.com/CENSUS/shadow/blob/master/pykd_engine.py
    if pykd.is64bitSystem():
        return 'x86-64'
    return 'x86'


def get_dword_size():
    global cache_dword_size
    if not cache_dword_size:
        arch = get_arch()
        if arch == 'x86':
            cache_dword_size = 4
        if arch == 'x86-64':
            cache_dword_size = 8
    return cache_dword_size


def read_dwords(addr, size):
    if get_dword_size() == 4:
        return pykd.loadDWords(addr, size)
    else:
        return pykd.loadQWords(addr, size)


def read_dword(addr):
    return read_dwords(addr, 1)[0]


def getProcessByName(name) -> int:
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
        symbol = f"{methodName}::`vftable'"
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
            self.vftable_methods.append([])
            while True:
                func_addr = read_dword(addr)
                symbol = pykd.findSymbol(func_addr)
                if symbol == f"{func_addr:x}":  # 没有找到symbol
                    break

                self.vftable_methods[index].append((addr, func_addr, symbol))
                addr = addr + get_dword_size()
        return self.vftable_methods

    def print_vftable_methods(self):
        vftable_methods = self.get_vftable_methods()
        for index, methods in enumerate(vftable_methods):
            print(f"######## {index}")
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
    length = 32 if pykd.is64bitSystem() else 24
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
    length = 32 if pykd.is64bitSystem() else 24
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
