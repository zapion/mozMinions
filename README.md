# Minions
This repository works for monitoring and logging for mobile devices.  It provides a watch dog daemon which reads configuration files and periodically/continuously fetch log from device.

# Getting started
Let's see a example from template.json

{
  "name": "b2g-info cmd",
  "serial": "",
  "command": "adb shell b2g-info"
}

Modify main() in boss.py and load this config.
