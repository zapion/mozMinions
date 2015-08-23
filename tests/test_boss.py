#!/usr/bin/python
from moz_minions.minions import ShellMinion, status
from moz_minions.boss import Boss

output = {'file': "unittest"}
mini = ShellMinion(name="test",
                   serial="123",
                   command="echo success",
                   output=output)

b = Boss()

def test_load():
    # TODO: create a random name file by pre-defined json
    pass

def test_report():
    # TODO
    pass
