from pykd import *
from common import *


def attach_process(process_name: str):
    pykd.initialize()
    pid = getProcessByName(process_name)
    if pid == 0:
        print(f"The app: {process_name} is not found")
        exit()

    print(f"Attaching to process: pid {pid}")
    pykd.attachProcess(pid)


class EntitySearcher:
    def __init__(self, class_name: str) -> None:
        self.class_name = class_name
        self.search_type = BaseType(class_name)

    def search(self) -> list[int]:
        self.search_type.print_vftable_methods()
        entity_addresses = getEntities(self.class_name)
        return entity_addresses

    def print_addr(self, entity_addresses: list[int]):
        ext = pykd.isWindbgExt()

        if entity_addresses:
            offsets = self.search_type.get_vftable_offsets(entity_addresses[0])
            print(', '.join([hex(x) for x in offsets]))

        if not ext:
            pykd.dprintln(
                "Found {} entities: ".format(len(entity_addresses)), True)
        else:
            pykd.dprintln(
                "<col fg=\"empfg\" bg=\"empbg\"><b>Found {} entities: </b></col>".
                format(len(entity_addresses)), True)

        def link(addr):
            return "<link cmd=\"dx ({0}*)0x{1:x}\">{1:x}</link>".format(
                self.class_name, addr)

        arr = []
        for addr in entity_addresses:
            if not ext:
                arr.append(f"{addr:x}")
            else:
                arr.append(link(addr))
            if (len(arr) == 10):
                pykd.dprintln(", ".join(arr), True)
                arr = []
        if (arr):
            pykd.dprintln(", ".join(arr), True)


def get_classname() -> str:
    return sys.argv[1] if pykd.isWindbgExt() else sys.argv[2]


def main():
    ext = pykd.isWindbgExt()

    try:
        if not ext:
            process_name = sys.argv[1]
            attach_process(process_name)

        class_name = get_classname()
        searcher = EntitySearcher(class_name)
        arr = searcher.search()
        searcher.print_addr(arr)
    except Exception as errtxt:
        print(errtxt)
    finally:
        if not ext:
            pykd.detachAllProcesses()


if __name__ == "__main__":
    main()
