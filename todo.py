import argparse
import copy
import logging
import os
import pprint
import psutil
import signal
import subprocess
import sys
import time

from typing import Tuple, Callable
from plyer import notification

class globals:
    table = {}
    items = {}

    @staticmethod
    def append(group: str, item: Tuple) -> None:
        globals.items.setdefault(group, []).append(item)

class defer_internal:
    def __init__(self, handler) -> None:
        self.handler = handler
    
    def __call__(self, generator) -> Callable:
        group = 'default'
        if generator in globals.table:
            group = globals.table[generator]

        globals.table[generator] = group

        for item in generator():
            hcopy = copy.copy(self.handler)
            globals.append(group, (generator, item, hcopy))
        
        return generator

class second_handler:
    def __init__(self, amount) -> None:
        self.amount = amount
        self.reset = amount

    def __call__(self) -> bool:
        self.amount = self.reset if self.amount <= 1 else self.amount - 1
        return self.amount == self.reset

class minute_handler(second_handler):
    def __init__(self, amount) -> None:
        super().__init__(60 * amount)

class hour_handler(second_handler):
    def __init__(self, amount) -> None:
        super().__init__(3600 * amount)

class schedule:
    @staticmethod
    def second(count: int) -> defer_internal:
        return defer_internal(second_handler(count))

    @staticmethod
    def minute(count: int) -> defer_internal:
        return defer_internal(minute_handler(count))
    
    @staticmethod
    def hour(count: int) -> defer_internal:
        return defer_internal(hour_handler(count))

class group_handler:
    def __init__(self, s: str) -> None:
        self.group = s

    def __call__(self, generator) -> Callable:
        if not generator in globals.table:
            globals.table[generator] = self.group
            return generator

        old = globals.table[generator]
        if old != self.group:
            move = []
            for item in globals.items[old]:
                if item[0] == generator:
                    move.append(item)

            for item in move:
                globals.items[old].remove(item)
                globals.append(self.group, item)

        return generator

def group(s: str):
    return group_handler(s)

def daemon(file: str) -> None:
    # Configure the logger
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                        level=logging.INFO,
                        datefmt='%H:%M:%S')

    # Check the arguments
    if len(sys.argv) == 1:
        print('No flags set, nothing will be done')
        return

    parser = argparse.ArgumentParser()
    parser.add_argument('--daemon', action='store_true')
    parser.add_argument('--kill', action='store_true')

    args = parser.parse_args(sys.argv[1:])
    if args.kill:
        count = 0
        basename = os.path.basename(file)
        for proc in psutil.process_iter():
            cmd = proc.cmdline()
            if proc.pid == os.getpid():
                continue

            if 'python' in cmd and basename in cmd:
                print('Found potential process', '`' + ' '.join(cmd) + '`')
                if input('Do you wish to terminate this process [y/n]? ') == 'y':
                    os.kill(proc.pid, signal.SIGTERM)
                    count += 1

        if count == 0:
            print('Found no processed of similar signature')

    if not args.daemon:
        return

    # Begin the daemon process
    logging.info('Launched todo daemon')
    pprint.pp(globals.items)

    # Sleep every second
    mtime = os.path.getmtime(file)
    print('mtime', file, mtime)
    while True:
        time.sleep(1)
        new_mtime = os.path.getmtime(file)
        if mtime < new_mtime:
            logging.info('Configuration has been refreshed')
            mtime = new_mtime
            ret = os.system(f'python {file}')
            if ret != 0:
                logging.error('Error running new configuration, skipping relaunch')
                # TODO: icon
                notification.notify('Todo', f'Error running new configuration ({file})', app_name='Todo')
            else:
                logging.warning('Verified configuration, relaunching with new one')
                subprocess.Popen(['python', file, '--daemon'])
                sys.exit(0)

        for group, items in globals.items.items():
            for _, task, handler in items:
                if handler():
                    logging.info(f'[{group}] Reminder for {task}')
                    notification.notify('Todo', f'[{group.upper()}]\nReminder for ({task})', app_name='Todo')

# Generate setup.py and run the installation
if __name__ == '__main__':
    setup = '''
    import setuptools

    setuptools.setup(name='todo',
                     scripts=['todo.py'],
                     version='1.0.0',
                     author='Venkataram',
                     license='MIT')
    '''

    lines = [ l[4:] + '\n' for l in setup.split('\n') ]
    with open('setup.py', 'w') as file:
        file.writelines(lines)

    os.system('pip install .')

