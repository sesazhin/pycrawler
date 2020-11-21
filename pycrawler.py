#!/usr/bin/env python3
import logging
import logging.handlers
import time

from genie.conf import Genie

from os import path
from os import mkdir

# To handle errors with connections to devices
from unicon.core import errors

from pathlib import Path


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


def create_non_existing_dir(dir_path):
    if not path.exists(dir_path):
        try:
            mkdir(dir_path)
        except PermissionError as e:
            log.error(f'Unable to create directory: {dir_path}.'
                      f'Insufficient privileges. Error: {e}')
            exit(1)


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


if __name__ == '__main__':
    main()


