import subprocess
import argparse
import sys
import re
from pexpect import popen_spawn, EOF, TIMEOUT
from colorama import init, Fore

init()


def get_processid_by_name(proc_name: str) -> list[int]:
    cmd = f'wmic process where name="{proc_name}" get processid'

    proc = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

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

    proc.stdout.close()
    proc.stderr.close()
    proc.kill()
    proc.wait()
    return processids


def execute_command(proc_name: str, command: str) -> bool:
    # TODO 仿照下面的例子写单元测试
    # https://github.com/pexpect/pexpect/blob/master/tests/test_popen_spawn.py

    processids = get_processid_by_name(proc_name)
    if not processids:
        print(f'{Fore.RED}ERROR{Fore.RESET}: The process "{proc_name}" is not found.')
        return False
    elif len(processids) > 1:
        print(f'{Fore.YELLOW}WARN{Fore.RESET}: More than one process is found by name "{proc_name}". '
              'Only the first one will be printed.')

    # cmd = f'cdb.exe -c ".logopen /t /u /d;{command};qd" -pv -p {processids[0]}'
    cmd = f'cdb.exe -c "{command};qd" -pv -p {processids[0]}'
    child = popen_spawn.PopenSpawn(cmd)
    need_print_line = False  # 在出现0:000>前都不打印出来

    while True:
        # expect_exact()和expect()是一样的，唯一不同的就是它的匹配列表中不再使用正则表达式。
        index = child.expect(['^0:000>', b'\n', EOF, TIMEOUT,
                             '^\s?quit:', ' error '], timeout=5)

        line = b''
        if index == 0:  # 遇到第一个prompt 0:000>
            need_print_line = True
        elif index == 2:  # cdb进程结束
            break
        elif index == 3:  # TIMEOUT, 等待用户的输入, 比如输入abc
            child.sendline('\n')
            need_print_line = False
        elif index == 4:  # 遇到quit命令
            need_print_line = False
        elif index == 5:  # 遇到error比如
            # 1. 输入了qwert等奇怪的命令。'Syntax error in'
            # 2. 执行命令uf module!function，如果有多个同名的函数。'Ambiguous symbol error at'
            line = child.before + child.after
            child.sendline('qd')
        else:
            line = child.before + child.after

        if need_print_line:
            content = line.decode()
            if content.startswith('*** WARNING: Unable to verify checksum for'):
                continue

            sys.stdout.write(content)
            sys.stdout.flush()

    # 不加的话有警告  ResourceWarning: unclosed file
    # 加上的话 单元测试就只能跑一个
    # sys.stderr.close()
    child.wait()
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('process_name', help="set the process name")
    parser.add_argument('command', help="set the windbg command", nargs='+')
    args = parser.parse_args()
    execute_command(args.process_name, ' '.join(args.command))


if __name__ == '__main__':
    main()
