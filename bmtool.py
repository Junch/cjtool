import re
from pathlib import Path

class StringRep:

    def __init__(self) -> None:
        self.words = set()
        self.matchObj = re.compile(r'(".+?")')

    def get_new_word(self, word) -> str:
        return  f"pfn{word[0].upper()}{word[1:]}"

    def replace(self, match_obj):
        if match_obj.group(0) is not None:
            word = match_obj.group(0)[1:-1] # Remove the " in the first and end
            self.words.add(word)
            return self.get_new_word(word)
        else:
            return match_obj.group(0)

    def parse(self, line) -> str:
        if re.search(r'#include.+\"(.+)\.h\"', line) or \
            re.search(r'\s.*DBG_WARN', line):
            return line
        else:
            # https://towardsdatascience.com/a-hidden-feature-of-python-regex-you-may-not-know-f00c286f4847
            new_line = self.matchObj.sub(self.replace, line)
            return new_line

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
