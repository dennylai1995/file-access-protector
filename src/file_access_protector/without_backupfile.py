import fcntl
import json
import time
import yaml

from functools import wraps

def file_lock(lock_type=fcntl.LOCK_EX):
    def decorator(fn):
        @wraps(fn)
        def wrapepr_func(*args, **kwargs):
            
            lock_file = args[0]
            retry_count = 0
            max_retry = 20
            wait_time = 0.05
            gain_lock = False
            result = None
            
            fd = open(lock_file, 'a+')
            
            try:
                while retry_count < max_retry:
                    try:
                        fcntl.flock(fd, lock_type | fcntl.LOCK_NB)
                        gain_lock = True
                        result = fn(*args, **kwargs)
                        break
                    except IOError:
                        retry_count += 1
                        print(f'!! Can not get lock for file [{lock_file}]! retrying [{retry_count}/{max_retry}]')
                        time.sleep(wait_time)
                    except Exception as e:
                        print(f'!! Error in file lock func: {e}')
                        break
                
                if gain_lock == False:
                    raise RuntimeError(f"Failed to get lock of file [{lock_file}]")
            finally:
                try:
                    fcntl.flock(fd, fcntl.LOCK_UN)
                except IOError:
                    pass
                fd.close()
            
            return result
        return wrapepr_func
    return decorator

@file_lock(fcntl.LOCK_SH)
def read_json(file_path):
    with open(file_path, 'r') as f:
        content = json.load(f)
    
    return content

@file_lock(fcntl.LOCK_EX)
def write_json(file_path, write_obj):
    with open(file_path, 'w') as f:
        json.dump(write_obj, f, indent=4)
        
@file_lock(fcntl.LOCK_SH)
def read_yaml(file_path):
    with open(file_path, 'r') as f:
        content = yaml.load(f, Loader=yaml.FullLoader)
    
    return content

@file_lock(fcntl.LOCK_EX)
def write_yaml(file_path, write_obj):
    with open(file_path, 'w') as f:
        yaml.dump(write_obj, f, sort_keys = False)