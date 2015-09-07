#!/usr/bin/python
import os
import glob
import shutil
import json
import time
import tempfile
from moz_minions.minions import ShellMinion, status
from moz_minions.boss import Boss

dirpath = tempfile.mkdtemp()
outdir = tempfile.mkdtemp()
b = Boss(dirpath=dirpath, output=outdir)
testfile = "test.json"


def dummy_touch():
    os.system("touch /tmp/mytest")


def test_load():
    testdata = {'name': 'mytest',
                'command': 'env',
                'interval': '1',
                'output': {'file': 'mytest'}}
    with open(testfile, "w") as oh:
        json.dump(testdata, oh)
    shutil.move(testfile, os.path.join(dirpath, testfile))
    time.sleep(2)
    query = os.path.join(outdir, 'mytest*')
    report = glob.glob(query)
    assert report is not None
    if report is not None:
        assert len(report) > 0
    os.remove(os.path.join(dirpath, testfile))
    for fp in glob.glob(os.path.join(outdir, "mytest*")):
        os.remove(fp)


def test_report():
    # TODO report has not yet implemented
    pass


def test_onstop():
    testdata = {'name': 'mytest',
                'command': 'env',
                'interval': '1',
                'output': {'file': 'mytest'}}
    with open(testfile, "w") as oh:
        json.dump(testdata, oh)
    shutil.move(testfile, os.path.join(dirpath, testfile))
    time.sleep(2)
    mini = b.workers.values()[0]
    mini.onstop = dummy_touch
    query = os.path.join(outdir, 'mytest*')
    report = glob.glob(query)
    assert report is not None
    if report is not None:
        assert len(report) > 0
    os.remove(os.path.join(dirpath, testfile))
    for fp in glob.glob(os.path.join(outdir, "mytest*")):
        os.remove(fp)
    time.sleep(1)
    ret = glob.glob('/tmp/mytest')
    assert ret
    if ret:
        os.remove("/tmp/mytest")
