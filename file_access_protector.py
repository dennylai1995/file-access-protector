import fcntl
import json
import os
import shutil
import subprocess
import time
from typing import Union

import psutil
import yaml

BACKUP_EXT = "_backup"


def get_lock_with_timeout(fd: int, timeout: float):
    # credit: https://stackoverflow.com/a/70424263
    # using exclusive lock here
    rc = subprocess.call(['flock',
                          '--timeout', str(timeout),
                          str(fd)],
                         pass_fds=[fd])

    if rc != 0:
        raise TimeoutError(f'Failed to get file lock')


def exclusive_lock(load, check_json):
    def Inner(fn):
        def wrapper_func(*args, **kwargs):

            result = None
            lock_file = args[0]
            timeout = 1  # second
            file_exist = True

            fn_start_time = 0
            fn_finish_time = 0
            lock_released_time = 0

            if load is True:
                if not os.path.isfile(lock_file):
                    raise AttributeError(f'Path [{lock_file}] is not a file!')
            else:
                # check data to dump
                if len(args) == 2 and type(args[1]) != list and type(args[1]) != dict:
                    raise AttributeError(
                        f'Data to dump must be list or dict ({args[1]})!')

            if check_json is True and not lock_file.endswith(".json"):
                raise AttributeError(
                    f'File name [{os.path.basename(lock_file)}] should have [.json] extension')

            try:
                f = open(lock_file, 'r')
            except IOError:
                # file not exist
                file_exist = False

            try:
                if file_exist:
                    get_lock_with_timeout(f.fileno(), timeout)

                fn_start_time = time.time()
                result = fn(*args, **kwargs)
                fn_finish_time = time.time()

            finally:
                if file_exist:
                    fcntl.flock(f, fcntl.LOCK_UN)
                    lock_released_time = time.time()
                    f.close()

                fn_time = fn_finish_time - fn_start_time
                if fn_time > 1:  # fn executed more than 1s
                    print(f'[{time.time()}] {fn.__name__}({lock_file}) performance -> [func_spent: {fn_time}s | lock_release_spent: {lock_released_time - fn_finish_time}s | func_start: {fn_start_time} | cpu: {psutil.cpu_percent()}% | mem: {psutil.virtual_memory().percent}% | disk: {psutil.disk_usage(os.path.dirname(lock_file)).percent}%]')

            return result

        return wrapper_func

    return Inner


@exclusive_lock(load=True, check_json=True)
def json_safe_load(file_path: str) -> Union[list, dict]:
    """
    Load json file safely

    Args:
        file_path (str): must be absolute path to the json file
    """

    backup_file_path = os.path.dirname(
        file_path) + "/" + os.path.basename(file_path).replace(".json", f'{BACKUP_EXT}.json')

    try:
        with open(file_path, 'r') as f:
            content = json.load(f)

        if type(content) != list and type(content) != dict:
            raise ValueError("JSON content is not list or dict!")

        # sync to backup file
        shutil.copy(file_path, backup_file_path)

    except Exception as e:
        print(f'!! json load file [{file_path}] failed ({e})')
        print(f'!! loading backup file [{backup_file_path}]...')

        if not os.path.isfile(backup_file_path):
            raise ValueError(f'Backup file [{backup_file_path}] not found!')

        with open(backup_file_path, 'r') as f:
            content = json.load(f)

        if type(content) != list and type(content) != dict:
            raise ValueError(
                "JSON content in backup file is not list or dict!")

        # sync back from backup file
        shutil.copy(backup_file_path, file_path)

        print(f'!! backup file [{backup_file_path}] loaded!')

    return content


@exclusive_lock(load=False, check_json=True)
def json_safe_dump(file_path: str, data: Union[list, dict]) -> None:
    """
    Dump data to json file safely (indent = 4)

    Args:
        file_path (str): must be absolute path to the json file
        data (Union[list, dict]): data to dump
    """

    backup_file_path = os.path.dirname(
        file_path) + "/" + os.path.basename(file_path).replace(".json", f'{BACKUP_EXT}.json')

    if not os.path.isfile(file_path):
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

        # create backup file
        shutil.copy(file_path, backup_file_path)

    else:
        with open(file_path, 'r') as f:
            content = json.load(f)

        if type(content) != list and type(content) != dict:
            raise ValueError("Original file content is not list or dict!")

        # make sure backup file synced with latest original file, in case dump fails
        shutil.copy(file_path, backup_file_path)

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

        # sync changes to backup file
        shutil.copy(file_path, backup_file_path)


@exclusive_lock(load=True, check_json=False)
def yaml_safe_load(file_path: str) -> Union[list, dict]:
    """
    Load yaml file safely

    Args:
        file_path (str): must be absolute path to the yaml file
    """

    file_name = os.path.basename(file_path)
    last_dot_index = file_name.rfind(".")
    backup_file_path = os.path.dirname(
        file_path) + "/" + file_name[:last_dot_index] + BACKUP_EXT + file_name[last_dot_index:]

    try:
        with open(file_path, 'r') as f:
            content = yaml.load(f, Loader=yaml.CLoader)

        if type(content) != list and type(content) != dict:
            raise ValueError("YAML content is not list or dict!")

        # sync to backup file
        shutil.copy(file_path, backup_file_path)

    except Exception as e:
        print(f'!! yaml load file [{file_path}] failed ({e})')
        print(f'!! loading backup file [{backup_file_path}]...')

        if not os.path.isfile(backup_file_path):
            raise ValueError(f'Backup file [{backup_file_path}] not found!')

        with open(backup_file_path, 'r') as f:
            content = yaml.load(f, Loader=yaml.CLoader)

        if type(content) != list and type(content) != dict:
            raise ValueError(
                "YAML content in backup file is not list or dict!")

        # sync back from backup file
        shutil.copy(backup_file_path, file_path)

        print(f'!! backup file [{backup_file_path}] loaded!')

    return content


@exclusive_lock(load=False, check_json=False)
def yaml_safe_dump(file_path: str, data: Union[list, dict]) -> None:
    """
    Dump data to yaml file safely (indent = 4)

    Args:
        file_path (str): must be absolute path to the yaml file
        data (_type_): data to dump
    """

    file_name = os.path.basename(file_path)
    last_dot_index = file_name.rfind(".")
    backup_file_path = os.path.dirname(
        file_path) + "/" + file_name[:last_dot_index] + BACKUP_EXT + file_name[last_dot_index:]

    if not os.path.isfile(file_path):
        with open(file_path, 'w') as f:
            yaml.dump(data, f, Dumper=yaml.CDumper, sort_keys=False, indent=4)

        # create backup file
        shutil.copy(file_path, backup_file_path)

    else:
        with open(file_path, 'r') as f:
            content = yaml.load(f, Loader=yaml.CLoader)

        if type(content) != list and type(content) != dict:
            raise ValueError("Original file content is not list or dict!")

        # make sure backup file synced with latest original file, in case dump fails
        shutil.copy(file_path, backup_file_path)

        with open(file_path, 'w') as f:
            yaml.dump(data, f, Dumper=yaml.CDumper, sort_keys=False, indent=4)

        # sync changes to backup file
        shutil.copy(file_path, backup_file_path)
