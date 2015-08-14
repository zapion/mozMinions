#!/usr/bin/python
from moz_minions.minions import ShellMinion, status

output = {'file': "unittest"}
mini = ShellMinion(name="test",
                   serial="123",
                   command="echo success",
                   output=output)


def test_create_minion():
    assert str(mini) == "{'output': {'file': 'unittest'}, 'serial': '123', 'command': 'echo success', 'name': 'test'}"


def test_collect():
    func = mini._output

    def nothing(self):
        pass
    mini._output = nothing
    expect = {'command': 'echo success',
              'name': 'test',
              'serial': '123',
              'status': status.ok,
              'stderr': '',
              'stdout': 'success\n'
              }
    actual = mini.collect()
    mini._output = func
    del actual['timestamp']
    assert actual == expect
