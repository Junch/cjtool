import pykd
import sys


class string:
    def __init__(self, addr):
        # _Mysize : size
        # _Myres  : capacity
        start = addr
        if pykd.is64bitSystem():
            (_Mysize, _Myres) = pykd.loadQWords(addr + 0x10, 2)
        else:
            (_Mysize, _Myres) = pykd.loadDWords(addr + 0x10, 2)
        if _Myres >= 0x10:
            start = pykd.ptrPtr(addr)
        self.buf = ""
        if _Mysize > 0:
            self.buf = pykd.loadChars(start, _Mysize)

    @classmethod
    def write(cls, addr, str):
        _Mysize = len(str)
        _Myres = _Mysize
        if _Myres >= 0x10:
            if pykd.is64bitSystem():
                pykd.writeQWords(addr, [addr + 32])
                pykd.writeCStr(addr + 32, str)
            else:
                pykd.writeDWords(addr, [addr + 24])
                pykd.writeCStr(addr + 24, str)
        else:
            _Myres = 0xf
            pykd.writeCStr(addr, str)
        if pykd.is64bitSystem():
            pykd.writeQWords(addr + 0x10, [_Mysize, _Myres])
        else:
            pykd.writeDWords(addr + 0x10, [_Mysize, _Myres])
        return cls(addr)

    def __str__(self):
        return self.buf

    def __repr__(self):
        return self.buf

    def __eq__(self, other):
        # https://stackoverflow.com/questions/4843173/how-to-check-if-type-of-a-variable-is-string
        if isinstance(other, self.__class__):
            return self.buf == other.buf
        elif type(other) == str:
            return self.buf == other
        else:
            return False


class wstring:
    def __init__(self, addr):
        start = addr
        if pykd.is64bitSystem():
            (_Mysize, _Myres) = pykd.loadQWords(addr + 0x10, 2)
        else:
            (_Mysize, _Myres) = pykd.loadDWords(addr + 0x10, 2)
        if _Myres >= 0x8:
            start = pykd.ptrPtr(addr)
        self.buf = ""
        if _Mysize > 0:
            self.buf = pykd.loadWChars(start, _Mysize)

    @classmethod
    def write(cls, addr, wstr):
        _Mysize = len(wstr)
        _Myres = _Mysize
        if _Mysize >= 0x8:
            if pykd.is64bitSystem():
                pykd.writeQWords(addr, [addr + 32])
                pykd.writeWStr(addr + 32, wstr)
            else:
                pykd.writeDWords(addr, [addr + 24])
                pykd.writeWStr(addr + 24, wstr)
        else:
            _Myres = 0x7
            pykd.writeWStr(addr, wstr)
        if pykd.is64bitSystem():
            pykd.writeQWords(addr + 0x10, [_Mysize, _Myres])
        else:
            pykd.writeDWords(addr + 0x10, [_Mysize, _Myres])  
        return cls(addr)

    def __str__(self):
        return self.buf

    def __repr__(self):
        return self.buf

    def __eq__(self, other):
        # https://stackoverflow.com/questions/4843173/how-to-check-if-type-of-a-variable-is-string
        if isinstance(other, self.__class__):
            return self.buf == other.buf
        elif type(other) == str:
            return self.buf == other
        else:
            return False


class vector:
    def __init__(self, addr, elemsize):
        self._arr = []
        if pykd.is64bitSystem():
            (myfirst, mylast, myend) = pykd.loadQWords(addr, 3)
        else:
            (myfirst, mylast, myend) = pykd.loadDWords(addr, 3)
        size = int((mylast - myfirst) / elemsize)
        self._capacity = (myend - myfirst) / elemsize
        for i in range(size):
            self._arr.append(myfirst + i * elemsize)

    def __len__(self):
        return len(self._arr)

    @property
    def capacity(self):
        return self._capacity

    def __getitem__(self, key):
        return self._arr[key]


class map_node:
    def __init__(self, addr):
        self.addr = addr
        if pykd.is64bitSystem():
            (self.left, self.parent, self.right) = pykd.loadQWords(addr, 3)
        else:
            (self.left, self.parent, self.right) = pykd.loadDWords(addr, 3)
        (self.color, self.isnil) = pykd.loadBytes(addr + 12, 2)

    def __str__(self):
        return "addr:{:x}, left:{:x}, parent:{:x}, right:{:x}, color:{:x},"
        " isnil:{:x}".format(self.addr, self.left, self.parent, self.right,
                             self.color, self.isnil)


class stlmap:
    def __init__(self, addr, keysize):
        self._dict = {}
        self._keysize = keysize
        if pykd.is64bitSystem():
            (head, size) = pykd.loadQWords(addr, 2)
        else:
            (head, size) = pykd.loadDWords(addr, 2)
        head_node = map_node(head)
        self.bintree_traverse(map_node(head_node.parent))

    def bintree_traverse(self, root):
        s = []
        node = root
        while not node.isnil or s:
            if not node.isnil:
                s.append(node)
                node = map_node(node.left)
            else:
                node = s.pop()
                self.add_dict(node)
                node = map_node(node.right)

    def add_dict(self, node):
        if pykd.is64bitSystem():
            key_addr = node.addr + 32
        else:
            key_addr = node.addr + 16
        val_addr = key_addr + self._keysize
        self._dict[key_addr] = val_addr

    @property
    def data(self):
        return self._dict


def test_map():
    if (len(sys.argv) == 1):
        print("Input the address of the map")
        return

    addr = int(sys.argv[1], 16)
    print(hex(addr))
    d = stlmap(addr, 4).data
    for key_addr, val_addr in d.items():
        key = pykd.loadDWords(key_addr, 1)[0]
        val = string(val_addr)
        print("{} -> {}".format(key, val))


if __name__ == "__main__":
    test_map()
