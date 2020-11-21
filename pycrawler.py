#!/usr/bin/env python3
import logging
import logging.handlers
import re
import time

from genie.conf import Genie

from os import path
from os import mkdir

# To handle errors with connections to devices
from unicon.core import errors

from pathlib import Path

from os import listdir
from os import remove
from os.path import isfile, join, getsize, basename
import pathlib

from datetime import datetime

def set_main_logging(logging_level_console='ERROR', logging_level_file='INFO') -> logging.getLogger():
    """
    Sets logger (for stderr, file).

    In case logging directory doesn't exist, will try to create it.
    If it's not possible to save to logging directory, will start to save to the directory with the script.

    :param DIRECTORY: Logging directory
    :param LOG_NAME: Logging file name
    :param LOG_FILE_SIZE: Size of each logging file in MBytes
    :return: link to the root logger object.
    """

    logging_level_to_num = {'CRITICAL': 50, 'ERROR': 40, 'WARNING': 30, 'INFO': 20, 'DEBUG': 10}

    logging_num_console = logging_level_to_num[logging_level_console]
    logging_num_file = logging_level_to_num[logging_level_file]

    global root_logger
    root_logger = logging.getLogger('main_logger')
    root_logger.propagate = False
    root_logger.setLevel(logging.DEBUG)
    logFormatter = logging.Formatter("%(asctime)s - %(filename)s - "
                                     "line %(lineno)s - %(funcName)s - %(levelname)s: %(message)s")

    # Initialize logging to console:
    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(logging_num_console)
    consoleHandler.setFormatter(logFormatter)
    root_logger.addHandler(consoleHandler)

    log_dir_name = 'log'
    script_directory = Path(__file__).resolve().parents[0]

    abs_log_path = path.join(script_directory, log_dir_name)
    create_non_existing_dir(abs_log_path)

    LOGFILE = path.join(abs_log_path, 'pycrawler.log')
    LOG_FILE_SIZE = 20

    try:
        # save logging output to file up to 20 Mbytes size,
        # keep 10 files in logging directory
        file_handler = logging.handlers.RotatingFileHandler(LOGFILE, maxBytes=(1048576 * LOG_FILE_SIZE), backupCount=10,
                                                            encoding='utf-8')
        file_handler.setLevel(logging_num_file)
        file_handler.setFormatter(logFormatter)
        root_logger.addHandler(file_handler)

    except PermissionError:
        root_logger.exception(f'Unable to create log file: {LOGFILE}.\nLogs not saved!')

    return root_logger


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


def create_non_existing_dir(dir_path):
    if not path.exists(dir_path):
        try:
            mkdir(dir_path)
        except PermissionError as e:
            log.error(f'Unable to create directory: {dir_path}.'
                      f'Insufficient privileges. Error: {e}')
            exit(1)


def remove_file(oldest_file) -> None:
    try:
        remove(oldest_file)
        log.info(f'oldest_file has been removed successfully: {oldest_file}')
    except PermissionError as e:
        log.error(f'Unable to delete gzip file: {oldest_file}.'
                  f'Insufficient privileges. Error: {e}')


def get_files_to_gz() -> List:
    dir_path = Path(__file__).resolve().parents[0]
    onlyfiles = [join(dir_path, f) for f in listdir(dir_path) if isfile(join(dir_path, f))]
    log.debug(f'onlyfiles: {onlyfiles}')

    only_non_gzip_files = [filepath for filepath in onlyfiles if '.gz' not in pathlib.Path(filepath).suffixes]

    log.debug(f'only_non_gzip_files: {only_non_gzip_files}')

    only_big_files = [filepath for filepath in only_non_gzip_files if getsize(filepath) > 500]

    log.debug(f'big_files: {only_big_files}')

    return only_big_files


def gzip_file(f_in_name: str, f_out_name: str) -> None:
    with open(f_in_name, 'rb') as f_in:
        with gzip.open(f_out_name, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)


def gz_files(only_big_files: List) -> None:
    # gz all plain text files and remove plain these plain text afterwards
    for big_file in only_big_files:
        timestamp = int(time.time())
        log.debug(f'big_file to gz: {big_file}')
        gzip_file(big_file, f'{big_file}_{timestamp}.gz')
        remove_file(big_file)


def remove_old_gz_files(only_big_files: List) -> None:
    dir_path = Path(__file__).resolve().parents[0]
    onlyfiles = [join(dir_path, f) for f in listdir(dir_path) if isfile(join(dir_path, f))]
    only_gzip_files = [filepath for filepath in onlyfiles if '.gz' in pathlib.Path(filepath).suffixes]

    for big_file in only_big_files:
        # get list of all .gz files for this big file with commands:
        gz_files_for_big_file = list(filter(lambda filepath: get_gzip_files(big_file, filepath), only_gzip_files))

        log.debug(f'only .gz files for this command output {big_file}: {gz_files_for_big_file}')

        # Check number of .gz files is not more than 'num_to_store'. Otherwise remove the oldest file:
        num_to_store = 10

        if len(file_list) > num_to_store:
            oldest_file = min(file_list)
            remove_file(oldest_file)


def write_commands_to_file(abs_filename, command_output, time_now_readable):
    try:
        with open(abs_filename, "a") as file_output:
            file_output.write(f'\n*****{time_now_readable}*****\n')
            log.debug(command_output)
            file_output.write(command_output)

    except IOError as e:
        log.error(f'Unable to write output to file: {abs_filename}.'
                  f'Due to error: {e}')
        exit(1)


def collect_device_commands(testbed, commands_to_gather, dir_name):
    abs_dir_path = path.join(path.dirname(__file__), dir_name)

    create_non_existing_dir(abs_dir_path)

    log.debug('Starting to collect output of the commands')

    for device_name, device in testbed.devices.items():
        # get operating system of a device from pyats_testbed.yaml
        device_os = device.os
        device_path = path.join(abs_dir_path, device_name)
        create_non_existing_dir(device_path)

        try:
            device.connect(log_stdout=False)
        except errors.ConnectionError:
            log.error(f'Failed to establish connection to: {device.name}.'
                      f'Check connectivity and try again.')
            continue

        time_now_readable = time.strftime('%d %b %Y %H:%M:%S', time.localtime())
        log.info(f'time_now: {time_now_readable}')

        if commands_to_gather.get(device_os):
            for command in commands_to_gather[device_os]:
                filename_command = command.replace(' ', '_')
                filename_command = filename_command.replace('*', 'all')
                filename = device_name + '_' + filename_command
                abs_filename = path.join(device_path, filename)
                log.info(f'filename: {abs_filename}')

                command_output = device.execute(command, log_stdout=True)
                
                # fixing cosmetic bug with '>' on the last line of FTD's output
                if device_os == 'fxos' and command_output[-1:] == '>':
                    command_output = '\n'.join(command_output.split('\n')[:-1]) + '\n'

                write_commands_to_file(abs_filename, command_output, time_now_readable)
        else:
            log.error(f'No commands for operating system: {device_os} '
                      f'of device: {device_name} has been defined. '
                      f'This device has been skipped. Specify list of commands'
                      f' for {device_os} and try again.')
            continue


def main():
    logging_level_console = 'ERROR'
    logging_level_file = 'INFO'
    script_directory = Path(__file__).resolve().parents[0]
    testbed_filename = f'{script_directory}/testbed.yaml'

    global log
    log = set_main_logging(logging_level_console, logging_level_file)

    log.debug(f'testbed_filename = {testbed_filename}')
    testbed = Genie.init(testbed_filename)

    commands_to_gather = {
        'fxos': ['show blocks', 'show blocks old', 'show blocks queue history detail',
                'show blocks queue history core-local', 'show blocks old core-local',
                'show blocks exhaustion snapshot', 'show blocks assigned', 'show blocks old dump | b 80']}

    dir_name = 'gathered_commands'

    collect_device_commands(testbed, commands_to_gather, dir_name)

    # get all big non-gz files (in plain text)
    only_big_files = get_files_to_gz()
    # gz all big plain text files
    gz_files(only_big_files)
    # remove the oldest gz file for each command
    remove_old_gz_files(only_big_files)


if __name__ == '__main__':
    main()


