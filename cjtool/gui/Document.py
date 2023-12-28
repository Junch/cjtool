import zipfile
import tempfile
import json
from pathlib import Path
from debuger import BreakPointHit, FunctionData
from PyQt5.Qt import QStandardItem, QIcon
from PyQt5.QtCore import pyqtSignal
import os


def keystoint(x):
    return {int(k): v for k, v in x.items()}


def zipDir(dirpath: str, outFullName: str) -> None:
    """
    压缩指定文件夹
    :param dirpath: 目标文件夹路径
    :param outFullName: 压缩文件保存路径+xxxx.zip
    :return: 无
    """
    zip = zipfile.ZipFile(outFullName, "w", zipfile.ZIP_DEFLATED)
    for path, dirnames, filenames in os.walk(dirpath):
        # 去掉目标跟路径，只对目标文件夹下边的文件及文件夹进行压缩
        fpath = path.replace(dirpath, '')

        for filename in filenames:
            zip.write(os.path.join(path, filename),
                      os.path.join(fpath, filename))
    zip.close()


class StandardItem(QStandardItem):
    def __init__(self, txt=''):
        super().__init__()
        self.setEditable(False)
        self.setText(txt)
        self.count = 1
        self.offset = 0
        self.id = 0
        self.functionData: FunctionData = None

    def increaseCount(self):
        self.count += 1
        txt = self.functionName()
        self.setText(f'{txt} * {self.count}')

    def functionName(self):
        arr = self.text().split('*')
        return arr[0].rstrip()


class Document(object):
    afterOpen = pyqtSignal()
    commentChange = pyqtSignal()

    def __init__(self, filename: str) -> None:
        self.tempdir = None
        self.filename = filename
        self.comment_icon = QIcon('image/comment.png')

    def open(self):
        zf = zipfile.ZipFile(self.filename)
        self.tempdir = tempfile.TemporaryDirectory()
        zf.extractall(self.tempdir.name)
        self.breakpoints, self.functions = self.__get_data()

    def close(self):
        if self.tempdir:
            self.tempdir.cleanup()
            self.tempdir = None

    def __get_data(self) -> tuple:
        assert self.tempdir
        monitor_file = Path(self.tempdir.name).joinpath('monitor.json')
        with open(monitor_file, 'r', encoding='utf-8') as f:
            data = json.loads(f.read())
            hits = data['hits']
            functions = keystoint(data['functions'])

            breakpoints = {}
            for item in hits:
                hit = BreakPointHit()
                hit.assign(item)
                breakpoints[hit.id] = hit

            functionDict = {}
            for k, v in functions.items():
                func = FunctionData()
                func.assign(v)
                func.offset = k  # 偏移量还是需要保存
                functionDict[k] = func
            return breakpoints, functionDict

    def __split_line(self, line: str) -> tuple:
        depth = 0
        for c in line:
            if c == '\t':
                depth = depth + 1
            else:
                break

        arr = line.split(' ')
        id = int(arr[0])
        fname = arr[1].rstrip()
        return depth, id, fname

    def get_source(self, functionData: FunctionData) -> str:
        source = ''
        src_filename = Path(self.tempdir.name).joinpath(
            'code', f"{functionData.offset}.cpp")
        if src_filename.exists():
            with open(src_filename.absolute(), 'r', encoding='utf-8') as f:
                source = f.read()
        else:
            source = functionData.content()  # 从源代码读入数据
        return source

    def fill_tree(self, rootNode: StandardItem) -> None:
        treefname = Path(self.tempdir.name).joinpath('tree.txt')
        with open(treefname, 'r', encoding='utf-8') as f:
            data = f.readlines()
            stack = [(-1, rootNode)]

            for line in data:
                depth, id, fname = self.__split_line(line)
                node = StandardItem(fname)
                node.id = id
                node.offset = self.breakpoints[id].offset
                node.functionData = self.functions[node.offset]

                cmt_filename = Path(self.tempdir.name).joinpath(
                    f"comment/{node.offset}.txt")
                if cmt_filename.exists():
                    node.setIcon(self.comment_icon)
                    with open(cmt_filename.absolute(), 'r', encoding='utf-8') as f:
                        comment = f.read()
                        node.functionData.comment = comment

                preDepth, preNode = stack[-1]
                while depth <= preDepth:
                    stack.pop()
                    preDepth, preNode = stack[-1]
                preNode.appendRow(node)
                stack.append((depth, node))

    def save(self, rootNode: StandardItem) -> None:
        src_dir = Path(self.tempdir.name).joinpath('code')
        if not src_dir.exists():
            Path(src_dir).mkdir()

        comment_dir = Path(self.tempdir.name).joinpath('comment')
        if not comment_dir.exists():
            Path(comment_dir).mkdir()

        lines = []
        stack = []
        stack.append((rootNode, -1))
        while stack:
            elem = stack[-1][0]
            depth = stack[-1][1]
            stack.pop()
            if hasattr(elem, 'functionData'):
                lines.append(
                    '\t'*depth + f"{elem.id} {elem.functionData.funtionName}\n")
                self.save_elem(elem)

            for row in range(elem.rowCount() - 1, -1, -1):
                child = elem.child(row, 0)
                stack.append((child, depth + 1))

        with open(Path(self.tempdir.name).joinpath('tree.txt').absolute(), 'w', encoding='utf-8') as f:
            f.writelines(lines)
        zipDir(self.tempdir.name, self.filename)

    def save_elem(self, elem: StandardItem) -> None:
        src_filename = Path(self.tempdir.name).joinpath(
            'code').joinpath(f"{elem.offset}.cpp")
        if not src_filename.exists():
            with open(src_filename.absolute(), 'w', encoding='utf-8') as f:
                content = elem.functionData.content()
                f.write(content)

        comment = elem.functionData.comment if hasattr(
            elem.functionData, 'comment') else ''
        cmt_filename = Path(self.tempdir.name).joinpath(
            'comment').joinpath(f"{elem.offset}.txt")
        if comment:
            with open(cmt_filename.absolute(), 'w', encoding='utf-8') as f:
                f.write(comment)
        else:
            if cmt_filename.exists():
                cmt_filename.unlink()
