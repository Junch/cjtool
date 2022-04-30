import subprocess
import argparse
import sys
import re
import pyperclip
from colorama import init, Fore

init()


def get_processid_by_name(proc_name: str) -> list[int]:
    cmd = f'wmic process where name="{proc_name}" get processid'

    proc = subprocess.Popen(cmd,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    processids = []
    while True:
        out = proc.stdout.readline()
        if proc.poll() is not None:
            break
        if out:
            line = out.decode()
            match_obj = re.match('^(\d+)', line)
            if match_obj:
                processid = int(match_obj.group(1))
                processids.append(processid)
    return processids


def print_call_stack(proc_name: str) -> int:
    processids = get_processid_by_name(proc_name)
    if not processids:
        print(
            f'{Fore.RED}ERROR{Fore.RESET}: The process "{proc_name}" is not found.'
        )
        return
    elif len(processids) > 1:
        print(
            f'{Fore.YELLOW}WARN{Fore.RESET}: More than one process is found by name "{proc_name}". '
            'Only the first one will be printed.')

    cmd = f'cdb.exe -c "kcn;qd" -pv -p {processids[0]}'

    proc = subprocess.Popen(cmd,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    content: str = ''

    while True:
        out = proc.stdout.readline()
        if proc.poll() is not None:
            break
        if out:
            line = out.decode()
            if re.search('^\d+\s.+', line):
                sys.stdout.write(line)
                sys.stdout.flush()
                content = content + line

    rc = proc.poll()

    if content:
        pyperclip.copy(content)
        print(
            f'{Fore.GREEN}NOTE{Fore.RESET}: The callstack has been copied to the clipboard.'
        )

    return rc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('process_name', help="set the process name")
    args = parser.parse_args()
    print_call_stack(args.process_name)


if __name__ == '__main__':
    main()
