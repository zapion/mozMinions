#!/usr/bin/python

import os
import time
from subprocess import Popen, PIPE
from enum import IntEnum
import json
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if len(logger.handlers) == 0:
    logger.addHandler(logging.StreamHandler())


class status(IntEnum):
    ok = 0
    warning = 1
    critical = 2
    unknown = 3

    def default(self, obj):
        return str(obj)

# TODO: factory pattern should work here?


def shell_cmd(cmd):
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    out = p.communicate()
    return {'stdout': out[0], 'stderr': out[1]}


class Minion(object):
    # An abtract class for spawning status collectors and emitters
    # 2 types of minions used
    # 1. periodical:
    #       parameter: interval
    #       will periodically trigger job
    #       ex: b2g-info, b2g-ps
    # 2. continuous:
    #       parameter: None
    #       will spawn subprocess
    # 2 func types:
    #       if func is string, run it as a system command
    name = ""
    kwargs = None
    serial = ""
    command = None
    description = ''

    def __init__(self, name, **kwargs):
        self.name = name
        self.update(**kwargs)

    def update(self, **kwargs):
        if 'name' in kwargs:
            self.name = kwargs['name']

        if 'serial' in kwargs:
            self.serial = kwargs['serial']
            os.environ['ANDROID_SERIAL'] = self.serial
        else:  # No serial assigned, should pop warning message
            pass
        if 'command' in kwargs:
            self.command = kwargs['command']
        if 'output' in kwargs:
            outdir = '.'
            if 'dirpath' in kwargs['output']:
                outdir = kwargs['output']['dirpath']
            if not os.path.isdir(outdir):
                logging.warning("direcotry not found: " + outdir + ", creating")
                os.makedirs(outdir)
            outfile = ''
            if 'file' in kwargs['output']:
                outfile = kwargs['output']['file']
            self.output_file = os.path.join(outdir,
                                            outfile)
        info_to_display = {k: kwargs.get(k, None) for k in ('serial',
                                                            'command',
                                                            'output')
                           }
        info_to_display['name'] = self.name
        self.description = str(info_to_display)
        success_file = kwargs['path'].replace('json', 'success')
        self.last_success_cmd = "touch " + os.path.join(outdir, success_file)

    def __str__(self):
        return self.description

    def _work(self, **kwargs):
        '''
        Abtract private interface
        Return dict with status code if work is done successfully
        '''
        raise NotImplementedError(
            "%s's worker function is not yet implemented." % (self.__class__)
            )

    def onstop(self):
        '''
        Abtract private interface
        Return dict with status code if work is done successfully
        '''
        pass

    def collect(self):
        '''
        interface for collecting information from monitored target
        Parameters: None
        Return: dict{}
        '''
        banana = {}
        try:
            ret = self._work()
            if ret:
                os.system(self.last_success_cmd)
            banana.update(ret)
            banana['name'] = self.name
            banana['serial'] = self.serial
            banana['status'] = status.ok
            banana['timestamp'] = time.time()
            if self.command:
                banana['command'] = self.command
        except Exception as e:
            banana['status'] = status.critical
            banana['err_msg'] = e.message
        self.banana = banana
        self._output(banana)
        return banana

    def report(self):
        '''
        TODO: if we use shinken or other framework they provide full
        stack of featureinterface for emitting state to file, DB,
        or other storage
        Parameters: None
        Return: True if emitting successfully
        '''
        print("test")
        return True

    def _output(self, data):
        '''
        Default output to files with timestamp
        '''
        timestamp = time.strftime('%Y-%m-%d-%H-%M-%S+0000', time.gmtime())
        filepath = self.output_file + "_" + timestamp
        with open(filepath, 'w') as oh:
            oh.write(json.dumps(data))
        return True


class ShellMinion(Minion):
    '''
    Minion for running shell command
    '''
    def _work(self):
        if self.command:
            return shell_cmd(self.command)
        return shell_cmd("adb shell b2g-ps")
