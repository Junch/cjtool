import re
from pathlib import Path
import argparse
from shutil import *
import shutil
import sys
from turtle import back
import pyperclip
from colorama import init, Fore, Back
init()


class StringRep:

    def __init__(self, prefix: str = 'pStr', inplace: bool = False, capitalize: bool = False) -> None:
        self.words = set()       # matched words
        self.wide_words = set()  # matched words with wide characters
        self.matchobj = re.compile(r'(L?"[a-zA-Z_]+\w+?")')

        self.prefix = prefix
        self.inplace = inplace
        self.capitalize = capitalize
        self.span_buffer = []

    def setPrefix(self, prefix: str) -> None:
        self.prefix = prefix

    def get_new_word(self, word) -> str:
        return f"{self.prefix}{word[0].upper()}{word[1:]}"

    def clear_span_buffer(self) -> None:
        self.span_buffer.clear()

    def replace(self, match_obj) -> str:
        content = match_obj.group(0)
        if content is None:
            return content

        self.span_buffer.append(match_obj.span())
        if content[0] == 'L':     # wide characters
            word = content[2:-1]  # remove the L" in the start and " in the end
            self.wide_words.add(word)
        else:
            word = content[1:-1]  # remove the " in the start and " in the end
            self.words.add(word)
        return self.get_new_word(word)

    def get_colored_line(self, line, num) -> str:
        arr = [0]
        for span in self.span_buffer:
            arr.append(span[0])
            arr.append(span[1])

        # https://stackoverflow.com/questions/10851445/splitting-a-string-by-list-of-indices
        colored_line = f"{Fore.RED}{num}{Fore.RESET}:"
        parts = [line[i:j] for i, j in zip(arr, arr[1:]+[None])]
        for index, part in enumerate(parts):
            if index % 2 == 0:
                part = f'{Fore.RESET}{part}'
            else:
                part = f'{Fore.GREEN}{part}'
            colored_line = colored_line + part
        return colored_line

    def parse(self, line: str, num: int = 0) -> str:
        if re.search(r'^\s*#include.+".+\.h"', line) or \
                re.search(r'^\s*[//,"]', line) or \
                re.search(r'^\s*DBG_WARN', line):
            return line
        else:
            # https://towardsdatascience.com/a-hidden-feature-of-python-regex-you-may-not-know-f00c286f4847
            new_line = self.matchobj.sub(self.replace, line)
            if new_line != line:
                print(self.get_colored_line(line, num))
                self.clear_span_buffer()
            return new_line

    def get_header_line(self, word: str, widechar: bool = False):
        newword = word
        if self.capitalize:
            newword = f'{word[0].upper()}{word[1:]}'
        line = ''
        if widechar:
            line = f'static constexpr wchar_t* {self.prefix}{newword} = L"{word}";'
        else:
            line = f'static constexpr char* {self.prefix}{newword} = "{word}";'
        return line

    def print_header_lines(self):
        content: str = ''
        for word in self.words:
            line = self.get_header_line(word)
            content = content + line + '\n'
            print(line)

        for word in self.wide_words:
            line = self.get_header_line(word, widechar=True)
            content = content + line + '\n'
            print(line)

        if content:
            pyperclip.copy(content)

            print(
                f"{Fore.RED}NOTE{Fore.RESET}: The content above has been copied to the clipboard.")

    def get_bak_name(self, filefullpath: str) -> str:
        filename = Path(filefullpath).name
        newfilepath = Path(filefullpath).with_name(f"{filename}.bak")
        if not newfilepath.is_file() and not newfilepath.is_dir():
            return newfilepath

        i = 0
        while True:
            i = i + 1
            newfilepath = Path(filefullpath).with_name(f"{filename}({i}).bak")
            if not newfilepath.is_file() and not newfilepath.is_dir():
                return newfilepath

    def parse_file(self, filefullpath: str) -> None:
        file_data = ''
        with open(filefullpath, 'r') as f:
            for num, line in enumerate(f, 1):  # start count from 1
                new_line = self.parse(line.rstrip(), num)
                file_data = file_data + new_line + '\n'

        if self.inplace:
            newfilepath = self.get_bak_name(filefullpath)
            shutil.copyfile(filefullpath, newfilepath)

            with open(filefullpath, 'w') as f:
                f.write(file_data)

        print('')
        self.print_header_lines()


def main():
    parser = argparse.ArgumentParser()
    parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter
    parser.add_argument('-i', '--inplace',
                        action='store_true', help="replace the file in place")
    parser.add_argument('-c', '--capitalize', action='store_true',
                        help="Capitalize the captured word")
    parser.add_argument('-p', '--prefix', default='pStr',
                        help="set the prefix for raw string")
    parser.add_argument('-f', '--file', required=True,
                        help="set the cpp file name")
    args = parser.parse_args()

    filefullpath = args.file
    if not Path(filefullpath).is_file():
        if Path.cwd().joinpath(filefullpath).is_file():
            filefullpath = Path.cwd().joinpath(filefullpath)
        else:
            print(f'{Fore.RED}Error{Fore.RESET}: File "{args.file}" is not found.')
            sys.exit(1)

    tool = StringRep(prefix=args.prefix, inplace=args.inplace,
                     capitalize=args.capitalize)
    tool.parse_file(filefullpath)


if __name__ == '__main__':
    main()
