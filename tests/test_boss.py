#!/usr/bin/python
import os
import glob
import shutil
import json
import time
import tempfile
import pytest
from moz_minions.boss import Boss

dirpath = tempfile.mkdtemp()
outdir = tempfile.mkdtemp()
testfile = "test.json"


@pytest.fixture()
def boss(request):
    b = Boss(dirpath=dirpath, output=outdir)
    def fin():
        shutil.rmtree(os.path.join(dirpath, testfile), ignore_errors=True)
        for fp in glob.glob(os.path.join(outdir, "mytest*")):
            shutil.rmtree(fp, ignore_errors=True)
        b.scheduler.shutdown()
    request.addfinalizer(fin)
    return b

def dummy_touch():
    os.system("touch /tmp/mytest")


def test_load(boss):
    testdata = {'name': 'mytest',
                'type': 'moz_minions.minions.ShellMinion',
                'command': 'env',
                'interval': '1',
                'output': {'file': 'mytest'}}
    with open(testfile, "w") as oh:
        json.dump(testdata, oh)
    query = os.path.join(outdir, 'mytest*')
    shutil.move(testfile, os.path.join(dirpath, testfile))
    time.sleep(2)
    report = glob.glob(query)
    assert report is not None
    if report is not None:
        assert len(report) > 0


def test_no_type(boss):
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
        assert len(report) == 0



def test_report():
    # TODO report has not yet implemented
    pass


def test_onstop(boss):
    testdata = {'name': 'mytest',
                'type': 'moz_minions.minions.ShellMinion',
                'command': 'env',
                'interval': '1',
                'output': {'file': 'mytest'}}
    with open(testfile, "w") as oh:
        json.dump(testdata, oh)
    shutil.copy2(testfile, os.path.join(dirpath, testfile))
    time.sleep(2)
    mini = boss.workers.values()[0]
    mini.onstop = dummy_touch
    time.sleep(2)
    query = os.path.join(outdir, 'mytest*')
    report = glob.glob(query)
    assert report is not None
    if report is not None:
        assert len(report) > 0
    os.remove(os.path.join(dirpath, testfile))
    time.sleep(5)
    ret = glob.glob('/tmp/mytest')
    assert ret
    if ret:
        os.remove("/tmp/mytest")
    shutil.move(testfile, os.path.join(dirpath, testfile))
