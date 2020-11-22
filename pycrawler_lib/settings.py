import os
import logging
from configparser import ConfigParser


def settings(ini_path):
    s = dict()
    s["file_size_to_gzip"] = 100
    s["num_to_store"] = 10
    s["logging_console"] = "ERROR"
    s["logging_file"] = "INFO"

    if os.path.exists(ini_path):
        try:
            config = ConfigParser()
            config.optionxform = str
            config.read(ini_path)
            if config.has_section("main"):
                opt_list = config.options("main")
                logging.debug(opt_list)
                for opt in s:
                    if opt in opt_list:
                        if opt in ["logging_console", "logging_file"]:
                            get_opt = config.get("main", opt)
                            get_opt = get_opt.upper()
                            if get_opt not in ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']:
                                 logging.error("Options 'logging_console' and 'logging_file' in settings.ini "
                                               "must be one of the following values: "
                                               "'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'. "
                                               "Setting default value.")

                            else:
                                s[opt] = get_opt

                        elif opt in ["file_size_to_gzip", "num_to_store"]:
                            get_opt = config.get("main", opt)
                            try:
                                get_opt = int(get_opt)
                                if get_opt <= 1000:
                                    s[opt] = get_opt
                                else:
                                    logging.error(f"Options 'file_size_to_gzip' and 'num_to_store' in settings.ini "
                                                  f"must be less than or equal to 1000. Setting default values: "
                                                  f"file_size_to_gzip: {s['file_size_to_gzip']} "
                                                  f"num_to_store: {s['num_to_store']}.")
                            except ValueError:
                                logging.error(f"Options 'file_size_to_gzip' and 'num_to_store' in settings.ini "
                                              f"must be numbers. Setting default values: "
                                              f"file_size_to_gzip: {s['file_size_to_gzip']} "
                                              f"num_to_store: {s['num_to_store']}.")

                        else:
                            s[opt] = config.get("main", opt)

        except Exception as err:
            logging.error(f"Unable to parse ini file - Error: {err}")

        return s

    else:
        logging.error(f"settings.ini file does not exist. Path checked: {ini_path}. Using default values.")

