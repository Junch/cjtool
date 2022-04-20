import re
from pathlib import Path

class StringRep:

    def __init__(self) -> None:
        self.words = set()

    def get_new_word(self, word) -> str:
        return  f"pfn{word[0].upper()}{word[1:]}"

    def parse(self, line) -> str:
        if re.search(r'#include.+\"(.+)\.h\"', line) or \
            re.search(r'\s.*DBG_WARN', line):
            return line
        else:
            matchObj = re.match(r'.+\"(.+?)\".*', line, re.M|re.I)
            if matchObj:
                word = matchObj.group(1)
                self.words.add(word)
                new_word = self.get_new_word(word)
                # headline = f"static constexpr wchar_t* {newWord} = L\"{word}\";"
                # print(headline)
                new_line = re.sub(r'\".+?\"', new_word, line)
                return new_line
            else:
                return line

    def parse_file(self, file):
        filename = Path(file).name
        newfile = Path(file).with_name(f"new{filename}")
        with open(newfile, "w") as nf:  
            with open(file, 'r') as f:
                for line in f:
                    new_line = self.parse(line, nf)
                    nf.write(new_line)

def main():
    tool = StringRep()
    tool.parse_file(r"D:\jinja2_study\filedata.cpp")

if __name__ == '__main__':
    main()
