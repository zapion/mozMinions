__author__ = 'shako'
import os
import copy
import json
import time
import logging
import psutil
import commands
import datetime
import tempfile

from minions import Minion


class MtbfToRaptorMinion(Minion):

    def update(self, **kwargs):
        Minion.update(self, **kwargs)
        self.conf = {}
        if 'job_info' in kwargs:
            for keyname in ['pid', 'program', 'jobname']:
                if keyname in kwargs['job_info']:
                    self.conf[keyname] = kwargs['job_info'][keyname]
                else:
                    raise Exception("Missing setting [%s] in \
                        configuration file!!!" % keyname)
            for keyname in ['host_name',
                            'port_no',
                            'user_name',
                            'pwd',
                            'database_name']:
                if keyname in kwargs['job_info']:
                    self.conf[keyname] = kwargs['job_info'][keyname]
                else:
                    logging.warning("Missing setting [%s] in \
                        configuration file!!!" % keyname)
        else:
            raise Exception("Missing job_info configuration setting \
                in your conf file!")

        self.path = kwargs['path']

        self.output_data = {}
        conf_name_list = os.path.splitext(os.path.basename(kwargs['path']))
        for data_name in ['mtbf', 'events']:
            output_file_path = os.path.join(kwargs['output']['dirpath'], conf_name_list[0] + "_" + data_name + ".json")
            self.output_data[data_name] = {'json_path': output_file_path,
                                           'data': None}

    def get_build_id(self):
        with tempfile.NamedTemporaryFile() as tmpFile:
            check_version_cmd = "b2g_check_versions -s %s \
                --log-json %s" % (self.serial, tmpFile.name)
            os.system(check_version_cmd)
            result = json.load(tmpFile)
            return result[self.serial]['Build ID']

    def get_device_crash_no(self):
        with tempfile.NamedTemporaryFile() as tmpFile:
            check_version_cmd = "b2g_get_crashreports -s %s \
                --log-json %s" % (self.serial, tmpFile.name)
            os.system(check_version_cmd)
            result = json.load(tmpFile)
            crash_file_list = []
            for keyname in ['PendingCrashReportsStdout',
                            'SubmittedCrashReportsStdout']:
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
            if result[build_id]['device_id'] == "0" or \
                    result[build_id]['build_id'] == "0":
                result.pop(build_id)
        return result

    def convert_datetime_to_timestamp(self,
                                      input_str,
                                      datetime_format="%Y%m%d%H%M%S"):
        datetime_obj = datetime.datetime.strptime(input_str, datetime_format)
        timestamp_obj = str((int(time.mktime(datetime_obj.timetuple()) * 1000) * 1000000) + 1)
        return timestamp_obj

    def get_running_time_in_hr(self):
        result = 0.0
        if os.path.exists(self.path):
            current_time = datetime.datetime.now()
            job_create_time = datetime.datetime.strptime(time.ctime(os.path.
                                                         getctime(self.path)),
                                                         "%a %b %d %H:%M:%S %Y")
            running_time = current_time - job_create_time
            result = running_time.total_seconds() / 60.0 / 60.0
        else:
            logging.warning("configure file [%s] is not exist!" % self.path)
        return result

    def generate_raptor_mtbf_data(self):
        build_configuration = self.conf['jobname'].split(".")
        result = {'key': self.name}
        result['fields'] = {"failures": self.get_device_crash_no(), "value": self.get_running_time_in_hr()}
        result['tags'] = {"device": build_configuration[0].replace("flamekk","flame-kk"),
                          "node": build_configuration[2],
                          "deviceId": self.serial,
                          "branch": build_configuration[1].replace("vmaster","master"),
                          "memory": build_configuration[3]}
        result['timestamp'] = self.convert_datetime_to_timestamp(self.get_build_id())
        return [result]

    def generate_raptor_event_data(self, mtbf_data):
        event_data = {"timestamp": mtbf_data[0]['timestamp'],
                      "tags": {"test": self.name,
                               "device": mtbf_data[0]['tags']['device'],
                               "memory": mtbf_data[0]['tags']['memory'],
                               "branch": mtbf_data[0]['tags']['branch'],
                               "title": "BuildId"},
                      "key": "annotation",
                      "fields": {"text": self.get_build_id()}}
        return [event_data]

    def _output(self, data):
        for keyname in ['mtbf', 'events']:
            if keyname in data:
                with open(data[keyname]['json_path'], "w") as json_output_file:
                    json.dump(data[keyname]['data'], json_output_file)
                    logging.info("Json file [%s] updated!" %
                                 data[keyname]['json_path'])
            else:
                logging.debug("output data : %s" % data)
                logging.warning("Missing key[%s] when data generating!!" %
                                keyname)

    def upload_raptor_data(self,
                           output_data,
                           host_name,
                           port_no,
                           user_name,
                           pwd,
                           database_name):
        cmd_format = "raptor submit %s --host %s --port %s --username \
                     %s --password %s --database %s --protocol https"
        for key_name in output_data.keys():
            if os.path.exists(output_data[key_name]['json_path']):

                cmd_str = cmd_format % (output_data[key_name]['json_path'],
                                        host_name,
                                        str(port_no),
                                        user_name,
                                        pwd,
                                        database_name)
                logging.debug("exeucte raptor cli command %s" % cmd_str)
                result = commands.getstatusoutput(cmd_str)
                if result[0] != 0:
                    logging.error("upload raptor data error: %s %s" % result)
                else:
                    logging.info("upload raptor data successfully!")
            else:
                logging.error("Json file is not exist!! Current json \
                              file path: %s" %
                              output_data[key_name]['json_path'])

    def check_process_exist(self):
        for process in psutil.process_iter():
            if process.pid == int(self.conf['pid']) and \
                    self.conf['program'] in process.cmdline():
                return True
        return False

    def _work(self):
        # check process exist, if exist, store the running time in tmp file,
        if self.check_process_exist():
            self.output_data['mtbf']['data'] = self.generate_raptor_mtbf_data()
            if len(self.output_data['mtbf']['data']) > 0:
                self.output_data['events']['data'] = \
                    self.generate_raptor_event_data(
                        self.output_data['mtbf']['data'])
                logging.debug("current result: %s" % self.output_data)
                return self.output_data
        # if not exist, kill the conf
        else:
            logging.info("process not exist!, continue to \
                         remove conf file %s" % self.path)
            if os.path.exists(self.path):
                os.remove(self.path)
                logging.info("conf file [%s] removed! " % self.path)

    def onstop(self):
        # submit the running time and data to raptor
        self.upload_raptor_data(self.output_data,
                                self.conf['host_name'],
                                self.conf['port_no'],
                                self.conf['user_name'],
                                self.conf['pwd'],
                                self.conf['database_name'])
