#!/usr/bin/python

import time
import json
from minions import Minion
from lib.b2g_crash_util import CrashAgent


class CrashMinion(Minion):
    def __init__(self, name, **kwargs):
        Minion.__init__(self, name, **kwargs)
        self.ca = CrashAgent(self.serial)

    def _work(self, **kwargs):
        # scan if has dump
        return self.ca.get_crash()

    def _output(self, data):
        # if sent, save crash-stat link
        # TODO if fail, try to get symbol and extract dump
        if 'crash_info' not in data:
            return False
        timestamp = time.strftime('%Y-%m-%d-%H-%M-%S+0000', time.gmtime())
        filepath = self.output_file + "_" + timestamp
        with open(filepath, 'w') as oh:
            oh.write(json.dumps(data))
        return True

    def onstop(self):
        # in case not missing anything, run _work and _output one more time.
        pass
