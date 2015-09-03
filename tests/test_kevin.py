__author__ = 'shako'
#!/usr/bin/python
import os
from moz_minions.kevin import MtbfToRaptorMinion


testdata = {'name': "mtbf",
            'output': {'dirpath': 'output',
                       'file': "unittest"},
            'serial': "2c0dc64c",
            'job_info': {
                'jobname':'flamekk.vmaster.moztwlab01.512',
                'seriesname':'mtbf',
                'pid': 18845,
                'program': "chrome",
                'path': "/home/shako/PycharmProjects/mozMinions/conf/test.json",
                'host_name': "mtbf-10",
                'port_no': 8086,
                'user_name': "xxxxxx",
                'pwd': "xxxxxx",
                'database_name': "raptor"
            }}

mini = MtbfToRaptorMinion(**testdata)

def test_generate_raptor_mtbf_data():
    mini.output_data['mtbf']['data'] = mini.generate_raptor_mtbf_data()
    print mini.output_data
    assert(mini.output_data['mtbf']['data']['mtbf'][0]['deviceId'] == testdata['serial'])

def test_generate_raptor_event_data():
    mini.output_data['events']['data'] = mini.generate_raptor_event_data(mini.output_data['mtbf']['data'])
    assert(mini.output_data['events']['data']['events'][0]['device'] == testdata['job_info']['jobname'].split(".")[0])

def test_create_json_files():
    mini.create_json_files(mini.output_data)
    assert(os.path.exists(mini.output_data['events']['json_path']))
    assert(os.path.exists(mini.output_data['mtbf']['json_path']))

def test_upload_raptor_data():
    mini.upload_raptor_data(mini.output_data, mini.conf['host_name'], mini.conf['port_no'],
                                        mini.conf['user_name'], mini.conf['pwd'], mini.conf['database_name'])

def test_flow():
    mini._work()

