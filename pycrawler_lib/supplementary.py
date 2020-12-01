import logging
import logging.handlers

from os import path
from os import mkdir
from pathlib import Path
from pyats.log import TaskLogHandler

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
    script_directory = Path(__file__).resolve().parents[1]

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

        pyats_handler = TaskLogHandler('/home/admin/pyats/pycrawler')
        root_logger.addHandler(pyats_handler)

    except PermissionError:
        root_logger.exception(f'Unable to create log file: {LOGFILE}.\nLogs not saved!')

    return root_logger


def create_non_existing_dir(dir_path):
    if not path.exists(dir_path):
        try:
            mkdir(dir_path)
        except PermissionError as e:
            root_logger.error(f'Unable to create directory: {dir_path}. Insufficient privileges. Error: {e}')
    else:
        root_logger.debug(f'directory {dir_path} already exists. No need to create')



