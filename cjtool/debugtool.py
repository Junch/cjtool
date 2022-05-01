import subprocess
import argparse
import sys
import re
from pexpect import popen_spawn, EOF
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


def execute_command(proc_name: str, command: str) -> bool:
    # TODO 仿照下面的例子写单元测试
    # https://github.com/pexpect/pexpect/blob/master/tests/test_popen_spawn.py

    processids = get_processid_by_name(proc_name)
    if not processids:
        print(
            f'{Fore.RED}ERROR{Fore.RESET}: The process "{proc_name}" is not found.'
        )
        return False
    elif len(processids) > 1:
        print(
            f'{Fore.YELLOW}WARN{Fore.RESET}: More than one process is found by name "{proc_name}". '
            'Only the first one will be printed.')

    cmd = f'cdb.exe -c "{command}" -pv -p {processids[0]}'
    child = popen_spawn.PopenSpawn(cmd)
    first_echo = True

    pre_line = ''
    while True:
        # expect_exact()和expect()是一样的，唯一不同的就是它的匹配列表中不再使用正则表达式。
        index = child.expect(
            ['^0:000>', b'\n', EOF, b'^[0-9a-fA-F]+`[0-9a-fA-F]+\s'],
            timeout=20)
        after_content = b''
        if child.after != EOF:
            after_content = child.after
        line = child.before + after_content
        if index == 0:
            if first_echo:
                first_echo = False
            else:
                line += b'qd\n'
                child.sendline('qd')
        elif index == 2:
            break  # 唯一正常退出的通道
        elif index == 3:
            if re.search(' cdb: Reading initial command', pre_line):
                child.sendline()

        sys.stdout.write(line.decode())
        sys.stdout.flush()
        pre_line = line.decode()
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('process_name', help="set the process name")
    parser.add_argument('command', help="set the windbg command", nargs='+')
    args = parser.parse_args()
    execute_command(args.process_name, ' '.join(args.command))


if __name__ == '__main__':
    main()
