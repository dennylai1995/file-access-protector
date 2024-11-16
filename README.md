# File Access Protector
![test coverage](./test/coverage-badge.svg)

A thread-safe json/yaml file loader/dumper with automatic file backup.

### Key Features
- Provide a thread-safe exclusive lock (using `fcntl`) on reading and writing a file
- Support JSON and YAML files
- Automatically create and sync to a backup file to avoid file corruption (ex. PC, without UPS, shuts down while writing to a file due to power outage)

### Limitations
- Writing to a non-existing file does not lock the file (due to file lock implementation with decorator)
- The file lock (`fcntl`) is an advisory lock which needs to be explicitly respected to by each process and thread accessing the file
- File path provided to those wrapper functions (`json_safe_load`, `json_safe_dump`, `yaml_safe_load`, `yaml_safe_dump`) must not contain `~`
- The file lock acquiring timeout is set to `1` second (feel free to adjust if it is too short)

### Tested Platform
- Python3.8 on Ubuntu 20.04