#!/usr/bin/env python3
import datetime
import gzip
import logging
import logging.handlers
import pathlib
import re
import shutil
import time

from genie.conf import Genie

from os import mkdir

from pathlib import Path

from os import listdir
from os import remove
from os.path import basename, dirname, exists, getsize, isfile, join

from typing import List
from typing import Dict

# To handle errors with connections to devices
from unicon.core import errors

import pycrawler_lib.settings as settings
import pycrawler_lib.supplementary as sup


def get_gzip_files(current_filename: str, filename_to_compare: str) -> str:
    filename = basename(current_filename)
    log.debug(f'filename: {filename}')

    str_to_match = rf'.*({filename}_\d{{10}}.gz)$'
    log.debug(f'str_to_match: {str_to_match}')

    r = re.compile(str_to_match)
    filepath = rf'{filename_to_compare}'
    if r.search(filepath):
        return (filepath)
    else:
        return ''


def remove_file(filename) -> None:
    try:
        remove(filename)
        log.info(f'File has been removed successfully: {filename}')
    except PermissionError as e:
        log.error(f'Unable to delete file: {filename}.'
                  f'Insufficient privileges. Error: {e}')


def get_files_to_gz(dir_path: str, file_size_to_gzip: int) -> List:
    onlyfiles = [join(dir_path, f) for f in listdir(dir_path) if isfile(join(dir_path, f))]
    log.debug(f'onlyfiles: {onlyfiles}')

    only_non_gzip_files = [filepath for filepath in onlyfiles if '.gz' not in pathlib.Path(filepath).suffixes]

    log.debug(f'only_non_gzip_files: {only_non_gzip_files}')

    file_size_to_gzip = file_size_to_gzip * 10 ** 6  # converting to Mbytes

    only_big_files = [filepath for filepath in only_non_gzip_files if getsize(filepath) > file_size_to_gzip]

    log.debug(f'big_files: {only_big_files}')

    return only_big_files


def gzip_file(f_in_name: str, f_out_name: str) -> None:
    with open(f_in_name, 'rb') as f_in:
        with gzip.open(f_out_name, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)


def gz_files(only_big_files: List, abs_archive_path: str) -> None:
    timestamp = int(time.time())

    # gz all plain text files and remove plain these plain text afterwards
    for big_file in only_big_files:
        log.debug(f'big_file to gz: {big_file}')

        big_filename = basename(big_file)
        gz_filename = f'{big_filename}_{timestamp}.gz'
        big_file_archived = join(abs_archive_path, gz_filename)

        gzip_file(big_file, big_file_archived)
        remove_file(big_file)


def remove_old_gz_files(only_big_files: List, dir_path: str, num_to_store) -> None:
    onlyfiles = [join(dir_path, f) for f in listdir(dir_path) if isfile(join(dir_path, f))]
    only_gzip_files = [filepath for filepath in onlyfiles if '.gz' in pathlib.Path(filepath).suffixes]

    for big_file in only_big_files:
        # get list of all .gz files for this big file with commands:
        gz_files_for_big_file = list(filter(lambda filepath: get_gzip_files(big_file, filepath), only_gzip_files))

        log.debug(f'only .gz files for this command output {big_file}: {gz_files_for_big_file}')

        if len(gz_files_for_big_file) > num_to_store:
            oldest_file = min(gz_files_for_big_file)
            remove_file(oldest_file)


def write_commands_to_file(abs_filename: str, command_output: str, time_now_readable: str, additional_info='') -> None:
    try:
        with open(abs_filename, "a") as file_output:
            file_output.write(f'\n*****{time_now_readable}. {additional_info}*****\n')
            log.debug(f'writing command output to file: {abs_filename}')
            file_output.write(command_output)

    except IOError as e:
        log.error(f'Unable to write output to file: {abs_filename}.'
                  f'Due to error: {e}')
        exit(1)


def get_failover_status(command_output):
    failover_status = None

    for failover_command_line in command_output.splitlines():
        failover_status = re.match(r'.*(This host: )(.*)', failover_command_line)
        if failover_status:
            failover_status = failover_status.group(2)
            break

    if not failover_status:
        failover_status = f'Unit failover status: {failover_status}'

    return failover_status


def collect_device_commands(testbed, commands_to_gather: Dict,
                            dir_name: str, file_size_to_gzip: int, num_to_store=10) -> None:
    abs_dir_path = join(dirname(__file__), dir_name)

    sup.create_non_existing_dir(abs_dir_path)

    log.debug('Starting to collect output of the commands')

    for device_name, device in testbed.devices.items():
        # get operating system of a device from pyats_testbed.yaml
        device_os = device.os
        device_path = join(abs_dir_path, device_name)
        sup.create_non_existing_dir(device_path)
        device_path_commands = join(device_path, 'commands')
        sup.create_non_existing_dir(device_path_commands)

        try:
            device.connect(log_stdout=False)
        except errors.ConnectionError:
            log.error(f'Failed to establish connection to: {device.name}.'
                      f'Check connectivity and try again.')
            continue

        time_now_readable = time.strftime('%d %b %Y %H:%M:%S', time.localtime())
        log.info(f'time_now: {time_now_readable}')

        if commands_to_gather.get(device_os):
            additional_info = ''
            # get failover state of this device
            if device_os == 'fxos':
                log.debug('running "show failover | include This host"')
                command_output = device.execute('show failover | include "This host"', log_stdout=False)
                additional_info = get_failover_status(command_output)  # get failover status
                log.info(f'Got failover status: {additional_info}')

            for command in commands_to_gather[device_os]:
                filename_command = command.replace(' ', '_')
                filename_command = filename_command.replace('*', 'all')
                filename = device_name + '_' + filename_command
                abs_filename = join(device_path_commands, filename)
                log.info(f'filename: {abs_filename}')

                command_output = device.execute(command, log_stdout=False)

                # fixing cosmetic bug with '>' on the last line of FTD's output
                if device_os == 'fxos' and command_output[-1:] == '>':
                    command_output = '\n'.join(command_output.split('\n')[:-1]) + '\n'
                write_commands_to_file(abs_filename, command_output, time_now_readable, additional_info)

            # get all big non-gz files (in plain text) for this device
            only_big_files = get_files_to_gz(device_path_commands, file_size_to_gzip)

            if len(only_big_files) > 0:
                archive_dir_name = 'archive'
                abs_archive_path = join(device_path_commands, archive_dir_name)
                sup.create_non_existing_dir(abs_archive_path)

                # gz all big plain text files for this device
                gz_files(only_big_files, abs_archive_path)
                # remove the oldest gz file for each command for this device
                remove_old_gz_files(only_big_files, abs_archive_path, num_to_store)

        else:
            log.error(f'No commands for operating system: {device_os} '
                      f'of device: {device_name} has been defined. '
                      f'This device has been skipped. Specify list of commands'
                      f' for {device_os} and try again.')
            continue


def collect_delta_device_commands(testbed, commands_to_gather: Dict,
                            dir_name: str, file_size_to_gzip: int, num_to_store=10) -> None:
    abs_dir_path = join(dirname(__file__), dir_name)

    sup.create_non_existing_dir(abs_dir_path)

    log.debug('Starting to collect output of the commands')

    for device_name, device in testbed.devices.items():
        # get operating system of a device from pyats_testbed.yaml
        device_os = device.os
        device_path = join(abs_dir_path, device_name)
        sup.create_non_existing_dir(device_path)
        device_path_delta = join(device_path, 'deltas')
        sup.create_non_existing_dir(device_path_delta)

        try:
            device.connect(log_stdout=False)
        except errors.ConnectionError:
            log.error(f'Failed to establish connection to: {device.name}.'
                      f'Check connectivity and try again.')
            continue

        time_now_readable = time.strftime('%d %b %Y %H:%M:%S', time.localtime())
        current_timestamp = int(time.time())
        skip_show_commands = False

        log.info(f'time_now: {time_now_readable}')

        if commands_to_gather.get(device_os):
            flag_delta_filename = join(Path(__file__).resolve().parents[1], '.clear_flag')

            if exists(flag_delta_filename):
                # counters have been cleared already
                log.info(f'flag_delta_filename {flag_delta_filename} exists')

                # check that we are able to read from delta file. Otherwise there is no point to collect show commands
                try:
                    with open(flag_delta_filename, mode='r') as fp:
                        clear_timestamp = fp.read()
                        clear_timestamp = int(clear_timestamp)
                except PermissionError as e:
                    log.error(f'Unable to read delta file: {flag_delta_filename}.'
                              f'Insufficient privileges. Error: {e}')
                    skip_show_commands = True

                except ValueError as e:
                    log.error(f'Unable to read delta file: {flag_delta_filename}.'
                              f'Non-integer value has been written or empty file. Error: {e}')
                    skip_show_commands = True

                if not skip_show_commands:
                    for command in commands_to_gather[device_os]:
                        filename_command = command[0].replace(' ', '_')
                        filename_command = filename_command.replace('*', 'all')
                        filename = device_name + '_' + filename_command
                        abs_filename = join(device_path_delta, filename)
                        log.info(f'filename: {abs_filename}')

                        command_output = device.execute(command[0], log_stdout=False)

                        log.info(f'Run command: "{command[0]}"')

                        additional_info = ''
                        # get failover state of this device
                        if device_os == 'fxos':
                            log.debug('running "show failover | include This host"')
                            command_output = device.execute('show failover | include "This host"', log_stdout=False)
                            additional_info = get_failover_status(command_output)  # get failover status
                            log.info(f'Got failover status: {additional_info}')

                        # fixing cosmetic bug with '>' on the last line of FTD's output
                        if device_os == 'fxos' and command_output[-1:] == '>':
                            command_output = '\n'.join(command_output.split('\n')[:-1]) + '\n'

                        clear_time_readable = datetime.datetime.fromtimestamp(clear_timestamp)
                        clear_time_readable = clear_time_readable.strftime('%d %b %Y %H:%M:%S')

                        seconds_interval = current_timestamp - clear_timestamp

                        delta_time_string = f'Delta output for the interval: ' \
                                            f'{clear_time_readable} - {time_now_readable}.' \
                                            f' Interval: {seconds_interval} sec'
                        write_commands_to_file(abs_filename, command_output, delta_time_string, additional_info)

                    # get all big non-gz files (in plain text) for this device
                    only_big_files = get_files_to_gz(device_path_delta, file_size_to_gzip)

                    if len(only_big_files) > 0:
                        archive_dir_name = 'archive'
                        abs_archive_path = join(device_path_delta, archive_dir_name)
                        sup.create_non_existing_dir(abs_archive_path)

                        # gz all big plain text files for this device
                        gz_files(only_big_files, abs_archive_path)
                        # remove the oldest gz file for each command for this device
                        remove_old_gz_files(only_big_files, abs_archive_path, num_to_store)

            else:
                # counters haven't been cleared already
                log.info(f'flag_delta_filename {flag_delta_filename} does not exist')

            # Block of run clear commands and update tmp file with new timestamp:
            for command in commands_to_gather[device_os]:
                device.execute(command[1], log_stdout=False)
                log.info(f'Run command: "{command[1]}"')

            try:
                with open(flag_delta_filename, mode='w') as fp:
                    fp.write(str(current_timestamp))
            except PermissionError as e:
                log.error(f'Unable to create delta file: {flag_delta_filename}.'
                          f'Insufficient privileges. Error: {e}')
                exit(1)
            # End of run clear commands and update tmp file with new timestamp


def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(filename)s - %(funcName)s - %(levelname)s - %(message)s')

    par_dir_path = Path(__file__).resolve().parents[1]
    settings_file_path = join(par_dir_path, 'config', 'settings.ini')

    s = settings.settings(settings_file_path)
    logging.debug(s)

    # file_size_to_gzip - Size (Mbytes) of file with commands to gzip
    file_size_to_gzip = s['file_size_to_gzip']

    # how many gzip files for each command to store
    num_to_store = s['num_to_store']

    # logging level for console
    logging_level_console = s['logging_console']

    # logging level for log file
    logging_level_file = s['logging_file']

    script_directory = Path(__file__).resolve().parents[1]
    testbed_filename = join(script_directory, 'config/testbed.yaml')

    global log
    log = sup.set_main_logging(logging_level_console, logging_level_file)

    if exists(testbed_filename):
        log.debug(f'testbed_filename = {testbed_filename}')
        testbed = Genie.init(testbed_filename)
    else:
        log.error(f"'testbed' file does not exist. Path checked: {testbed_filename}. Exiting")
        exit(1)

    commands_to_gather = {
        'fxos': ['show blocks', 'show blocks old', 'show blocks queue history detail',
                'show blocks queue history core-local', 'show blocks old core-local',
                'show blocks exhaustion snapshot', 'show blocks assigned', 'show blocks old dump | b 80']}

    dir_name = join(script_directory, 'gathered_commands')
    delta_commands_to_gather = {
            'fxos': [('show asp drop', 'clear asp drop'),
                     ('show crypto accelerator statistics',
                     'clear crypto accelerator statistics')]}

    collect_device_commands(testbed, commands_to_gather, dir_name, file_size_to_gzip, num_to_store)
    collect_delta_device_commands(testbed, delta_commands_to_gather, dir_name, file_size_to_gzip, num_to_store)


if __name__ == '__main__':
    main()


