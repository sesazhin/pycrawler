#!/usr/bin/env python3
import logging

from genie.conf import Genie

from os import path
from os import mkdir

# To handle errors with connections to devices
from unicon.core import errors

from pathlib import Path

def create_non_existing_dir(dir_path):
    if not path.exists(dir_path):
        try:
            mkdir(dir_path)
        except PermissionError as e:
            log.error(f'Unable to create directory: {dir_path}.'
                      f'Insufficient privileges. Error: {e}')
            exit(1)


def write_commands_to_file(abs_filename, command_output):
    try:
        with open(abs_filename, "w") as file_output:
            file_output.write(command_output)

    except IOError as e:
        log.error(f'Unable to write output to file: {abs_filename}.'
                  f'Due to error: {e}')
        exit(1)


def collect_device_commands(testbed, commands_to_gather, dir_name):
    abs_dir_path = path.join(path.dirname(__file__), dir_name)

    create_non_existing_dir(abs_dir_path)

    log.info('Starting to collect output of the commands')

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

        if commands_to_gather.get(device_os):
            for command in commands_to_gather[device_os]:
                filename_command = command.replace(' ', '_')
                filename_command = filename_command.replace('*', 'all')
                filename = device_name + '_' + filename_command
                abs_filename = path.join(device_path, filename)
                log.info(f'filename: {abs_filename}')

                command_output = device.execute(command, log_stdout=True)

                write_commands_to_file(abs_filename, command_output)
        else:
            log.error(f'No commands for operating system: {device_os} '
                      f'of device: {device_name} has been defined. '
                      f'This device has been skipped. Specify list of commands'
                      f' for {device_os} and try again.')
            continue


def main():
    global log
    format = '%(asctime)s - %(filename)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=format)

    log = logging.getLogger(__name__)

    script_directory = Path(__file__).resolve().parents[0]

    testbed_filename = f'{script_directory}/testbed.yaml'
    log.info(f'testbed_filename = {testbed_filename}')
    testbed = Genie.init(testbed_filename)

    commands_to_gather = {
        'fxos': ['show blocks', 'show blocks old', 'show blocks queue history detail',
                'show blocks queue history core-local', 'show blocks old core-local',
                'show blocks exhaustion snapshot', 'show blocks assigned', 'show blocks old dump | b 80']}

    dir_name = 'gathered_commands'

    collect_device_commands(testbed, commands_to_gather, dir_name)


if __name__ == '__main__':
    main()
