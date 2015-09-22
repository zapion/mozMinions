# Minions
This repository works for monitoring and logging for mobile devices.  It provides a watch dog daemon which reads configuration files and periodically/continuously fetch log from device.

# Getting started
Let's see a example from template.json

{
  "name": "b2g-info cmd",
  "type": "",
  "serial": "",
  "command": "adb shell b2g-info"
}

Modify main() in boss.py and load this config.

# Usage
Two command line parameters for boss.py
1. dirpath: default value is current directory.  it indicates directory for job queue.  Any adding/modifying/removing json file will affect job queue in monitoring scheduler.
2. output: specify where the output file should be stored. It will create ./output by default.

# Job settings
name: an identifier for user
type: class path for monitoring agent
serial: device serial number
command: used for default shell script agent
