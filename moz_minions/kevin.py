__author__ = 'shako'
import os
import copy
import json
import time
import psutil
import commands
import datetime
import tempfile

from minions import Minion

class MtbfToRaptorMinion(Minion):

    def update(self):
        Minion.update(self)
        self.conf = {}
        if 'job_info' in self.kwargs:
            for keyname in ['pid', 'program', 'path', 'jobname']:
                if keyname in self.kwargs['job_info']:
                    self.conf[keyname] = self.kwargs['job_info'][keyname]
                else:
                    raise Exception("Missing setting [%s] in configuration file!!!" % keyname)
            for keyname in ['host_name', 'port_no', 'user_name', 'pwd', 'database_name']:
                if keyname in self.kwargs['job_info']:
                    self.conf[keyname] = self.kwargs['job_info'][keyname]
                else:
                    print "Missing setting [%s] in configuration file!!!" % keyname
        else:
            raise Exception("Missing job_info configuration setting in your conf file!")

        self.output_data = {}
        for data_name in ['mtbf', 'events']:
            output_file_name = str(self.conf['pid']) + "_" + data_name + ".json"
            output_file_path = os.path.join(self.outdir, output_file_name)
            self.output_data[data_name] = {'json_path': output_file_path, 'data': None}

    def get_build_id(self):
        with tempfile.NamedTemporaryFile() as tmpFile:
            check_version_cmd = "b2g_check_versions -s %s --log-json %s" % (self.serial, tmpFile.name)
            os.system(check_version_cmd)
            result = json.load(tmpFile)
            return result[self.serial]['Build ID']

    def get_device_crash_no(self):
        with tempfile.NamedTemporaryFile() as tmpFile:
            check_version_cmd = "b2g_get_crashreports -s %s --log-json %s" % (self.serial, tmpFile.name)
            os.system(check_version_cmd)
            result = json.load(tmpFile)
            crash_file_list = []
            for keyname in ['PendingCrashReportsStdout', 'SubmittedCrashReportsStdout']:
                line_list = result[keyname].split('\n')
                for line in line_list:
                    if "No such" not in line:
                        crash_file_name = line.split(" ")[-1].split(".")[0]
                        if crash_file_name not in crash_file_list:
                            crash_file_list.append(crash_file_name)

            crash_no = len(crash_file_list)
            return crash_no

    def get_device_info(self, job_detail):
        result = copy.deepcopy(job_detail)
        for build_id in job_detail.keys():
            result[build_id]['device_id'] = self.serial
            result[build_id]['build_id'] = self.get_build_id()
            result[build_id]['crash_no'] += self.get_device_crash_no()
            if result[build_id]['device_id'] == "0" or result[build_id]['build_id'] == "0":
                result.pop(build_id)
        return result

    def convert_datetime_to_timestamp(self, input_str, datetime_format="%Y%m%d%H%M%S"):
        datetime_obj = datetime.datetime.strptime(input_str, datetime_format)
        timestamp_obj = time.mktime(datetime_obj.timetuple()) * 1000
        return timestamp_obj

    def get_running_time_in_hr(self):
        current_time = datetime.datetime.now()
        job_create_time = datetime.datetime.strptime(time.ctime(os.path.getctime(self.conf['path'])), "%a %b %d %H:%M:%S %Y")
        running_time = current_time - job_create_time
        return running_time.total_seconds() / 60.0 / 60.0

    def generate_raptor_mtbf_data(self):
        build_configuration = self.conf['jobname'].split(".")
        result = {self.name: []}
        insert_dict = {}
        insert_dict['model'] = build_configuration[0]
        insert_dict['branch'] = build_configuration[1]
        insert_dict['node'] = build_configuration[2]
        insert_dict['memory'] = build_configuration[3]
        insert_dict['runningHr'] = self.get_running_time_in_hr()
        insert_dict['buildid'] = self.get_build_id()
        insert_dict['time'] = self.convert_datetime_to_timestamp(insert_dict['buildid'])
        insert_dict['crashNo'] = self.get_device_crash_no()
        insert_dict['deviceId'] = self.serial
        result[self.name].append(insert_dict)
        return result

    def generate_raptor_event_data(self, mtbf_data):
        tmp_list = self.conf['jobname'].split(".")
        branch_name = tmp_list[1]
        device_name = tmp_list[0]
        memory_set = tmp_list[3]
        event_data = {'events': [{"title": "buildInfo",
                                  "text": "buildid: " + mtbf_data[self.name][0]['buildid'],
                                  "time": mtbf_data[self.name][0]['time'],
                                  "tags": None,
                                  "branch": branch_name,
                                  "device": device_name,
                                  "memory": memory_set
                                  }]}
        return event_data

    def create_json_files(self, data):
        for keyname in data.keys():
            with open(data[keyname]['json_path'], "w") as json_output_file:
                json.dump(data[keyname]['data'], json_output_file)

    def upload_raptor_data(self, output_data, host_name, port_no, user_name, pwd, database_name):
        cmd_format = "raptor submit %s --host %s --port %s --username %s --password %s --database %s"
        for key_name in output_data.keys():
            if os.path.exists(output_data[key_name]['json_path']):
                cmd_str = cmd_format % (output_data[key_name]['json_path'], host_name, str(port_no), user_name, pwd, database_name)
                result = commands.getstatusoutput(cmd_str)
                if result[0] != 0:
                    print "upload raptor data error: %s %s" % result
                else:
                    print "upload raptor data successfully!"
            else:
                print "Json file is not exist!!"

    def check_process_exist(self):
        for process in psutil.process_iter():
            if process.pid == int(self.conf['pid']) and self.conf['program'] in process.name():
                return True
        return False

    def _work(self):
        #check process exist, if exist, store the running time in tmp file,
        if self.check_process_exist():
            self.output_data['mtbf']['data'] = self.generate_raptor_mtbf_data()
            if len(self.output_data['mtbf']['data']) > 0:
                self.output_data['events']['data'] = self.generate_raptor_event_data(self.output_data['mtbf']['data'])
                self.create_json_files(self.output_data)
                print "current result: %s" % self.output_data

        # if not exist, kill the conf,  submit the running time and data to raptor
        else:
                self.upload_raptor_data(self.output_data, self.conf['host_name'], self.conf['port_no'],
                                        self.conf['user_name'], self.conf['pwd'], self.conf['database_name'])
                if os.path.exists(self.conf['path']):
                    os.remove(self.conf['path'])

