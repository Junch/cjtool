import re
from pathlib import Path

class StringRep:

    def __init__(self) -> None:
        self.words = set()
        self.matchObj = re.compile(r'("[a-zA-Z_]+\w+?")')

    def get_new_word(self, word) -> str:
        return  f"pfn{word[0].upper()}{word[1:]}"

    def replace(self, match_obj) -> str:
        if match_obj.group(0) is not None:
            word = match_obj.group(0)[1:-1] # Remove the " in the first and end

            self.words.add(word)
            return self.get_new_word(word)
        else:
            return match_obj.group(0)

    def print_line(self, line, num) -> None:
        print(f"{num}:{line[:-1]}")

    def parse(self, line: str, num: int = 0) -> str:
        if re.search(r'\s*#include.+".+\.h"', line) or \
           re.search(r'\s*//', line) or \
           re.search(r'\s*DBG_WARN', line):
            return line
        else:
            # https://towardsdatascience.com/a-hidden-feature-of-python-regex-you-may-not-know-f00c286f4847
            new_line = self.matchObj.sub(self.replace, line)
            if new_line != line:
                self.print_line(line, num)
            return new_line

    def parse_file(self, file) -> None:
        filename = Path(file).name
        newfile = Path(file).with_name(f"{filename}.bak")
        with open(newfile, "w") as nf:  
            with open(file, 'r') as f:
                for num, line in enumerate(f, 1): # start count from 1
                    new_line = self.parse(line, num)
                    nf.write(new_line)

def main():
    tool = StringRep()
    tool.parse_file(r"D:\jinja2_study\filedata.cpp")

if __name__ == '__main__':
    main()
