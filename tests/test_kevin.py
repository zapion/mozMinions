#!/usr/bin/python
__author__ = 'shako'

from moz_minions.kevin import MtbfToRaptorMinion
from b2g_util.util.adb_helper import AdbWrapper


testdata = {'name': "mtbf",
            'path': "/home/shako/PycharmProjects/mozMinions/conf/test.json",
            'output': {'dirpath': 'output',
                       'file': "unittest"},
            'serial': "",
            'job_info': {
                'jobname': 'flamekk.vmaster.moztwlab01.512',
                'seriesname': 'mtbf',
                'pid': 18845,
                'program': "chrome",
                'host_name': "mtbf-10",
                'port_no': 8086,
                'user_name': "xxxxxx",
                'pwd': "xxxxxx",
                'database_name': "raptor"
            }}

# FIXME: with following workaround we still need at least one device connected
devices = AdbWrapper.adb_devices().keys()
testdata['serial'] = devices[0]
mini = MtbfToRaptorMinion(**testdata)


def test_generate_raptor_mtbf_data():
    data = mini.output_data['mtbf']['data'] = mini.generate_raptor_mtbf_data()
    assert(data['mtbf'][0]['deviceId'] == testdata['serial'])


def test_generate_raptor_event_data():
    mini.output_data['events']['data'] = mini.generate_raptor_event_data(
        mini.output_data['mtbf']['data'])
    data = mini.output_data['events']['data']
    assert(data['events'][0]['device']
           == testdata['job_info']['jobname'].split(".")[0])


def test_upload_raptor_data():
    mini.upload_raptor_data(mini.output_data,
                            mini.conf['host_name'],
                            mini.conf['port_no'],
                            mini.conf['user_name'],
                            mini.conf['pwd'],
                            mini.conf['database_name'])


def test_flow():
    mini._work()
