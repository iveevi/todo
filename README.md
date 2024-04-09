# todo

Configure tasks and reminders using Python.

## Install

`python todo.py`

This will generate a `setup.py` file and then run `pip install .` to install
the package `todo`.

## Example

An example configuration is shown below as `tasks.py`.

```py
import todo

@todo.group('class A')
@todo.schedule.minute(20)
def classA():
	return ['homework1', 'project0']

@todo.group('class B')
@todo.schedule.hour(2)
def classB():
	return ['pa1', 'read the slides']

if __name__ == '__main__':
    todo.daemon(__file__)
```

To launch the daemon, run `python tasks.py --daemon`. The original file can be
updated without interupting the daemon. The new configuration will take effect
as soon as a working (e.g. runs without errors) save takes effect.

To terminate the daemon, run `python tasks.py --kill` which will scan similar
looking processes.

## Features

**Implemented:**
- [x] Hourly, minute-ly and second-ly (?) reminders
- [x] Live configruation updates
- [x] Grouping tasks using `@todo.group(...)`

**Upcoming:**
- [ ] Date based scheduling
- [ ] Sound-based notifications
