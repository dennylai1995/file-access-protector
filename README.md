# 📂 File Access Protector
![test coverage](./src/tests/coverage-badge.svg)

A thread-safe json/yaml file loader/dumper with automatic file backup.

## 🎯 Key Features
- Provide a thread-safe exclusive lock (using `fcntl`) on reading and writing a file
- Support JSON and YAML files
- Automatically create and sync to a backup file to avoid file corruption (ex. PC, without UPS, shuts down while writing to a file due to power outage)

## ❗ Limitations
- The file lock (`fcntl`) is an advisory lock which needs to be explicitly respected to by each process and thread accessing the file
- File path provided to those wrapper functions (`json_safe_load`, `json_safe_dump`, `yaml_safe_load`, `yaml_safe_dump`) must not contain `~`
- The file lock acquiring timeout is set to `1` second (feel free to adjust if it is too short)

## 🧠 Some Knowledge
On linux, there are two kinds of file locks:
- Mandatory lock 
    - enforced by kernel
    - require mounting filesystem with `mand` option + change mode (`chmod`) of target files
- Advisory lock
    - processes/threads need to explicitly respect to the lock
    - use `flock` (command line) or `fcntl` (library, for granular control)

A lock can have two modes:
- shared lock (aka read lock)
    - An active shared lock blocks the acquisition of a exclusive lock
    - Multiple active shared locks on a file is allowed
- exclusive lock (aka write lock)
    - An active exclusive lock blocks the acquisition of a shared lock
    - A file can ONLY have ONE active exclusive lock


| 2nd LOCK | 1st shared lock | 1st exclusive lock |
|:-----:|:------:|:-------:|
| shared lock | ✅ | ❌ |
| exclusive lock | ❌ | ❌ |


## 🤔 Think Deeper
The result this repo achieves is
- To avoid a file being read while a write action is in progress
- To avoid multiple write actions applying to the same file simultaneously

Well, maybe those are some of the reasons database system were invented.

## 🧪 Tested Platform
- Python3.8 on Ubuntu 20.04