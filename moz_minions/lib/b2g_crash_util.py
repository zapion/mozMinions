#!/usr/bin/python

import sys
import os
import subprocess
import re
import urllib2
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
from b2g_util.util.adb_helper import AdbWrapper


SUBMIT_URL = "https://crash-reports.mozilla.com/submit"
REPORT_URL = "https://crash-stats.mozilla.com/report/index/"
BASE_DIR = "/data/b2g/mozilla/Crash Reports/"


def get_current_all_dev_serials():
    devices = []
    p = subprocess.Popen(['adb', 'devices'], stdout=subprocess.PIPE)
    res = p.communicate()[0].split('\n')
    res.pop(0)
    for li in res:
        m = re.search('(\w+)', li)
        if(m is not None):
            devices.append(m.group(0))
    return devices


class CrashAgent(object):
    def __init__(self, serial):
        # TODO get more build info
        self.serial = serial

    def __len__(self):
        crash = self.get_crash()
        return len(crash['submitted'] + crash['pending'])

    def fetch_crash_info(self):
        scan_cmd = ['adb', '-s', self.serial, 'shell', 'ls -l']
        submit_dir = BASE_DIR + 'submitted'
        pending_dir = BASE_DIR + 'pending'
        p = subprocess.Popen(scan_cmd + [submit_dir],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        output = p.communicate()[0]
        submitted_set = set()
        if "No such" not in output:
            for out in output.split('\n'):
                if not out.strip():
                    continue
                cid = re.search('\sbp-(\S+)\.txt.?$',
                                out.split(" ")[-1].strip()).group(1)
                if cid not in submitted_set:
                    submitted_set.add(REPORT_URL + cid)

        q = subprocess.Popen(scan_cmd + [pending_dir],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        output = q.communicate()[0]
        pending_set = set()
        if "No such" not in output:
            for out in output.split('\n'):
                if not out.strip():
                    continue
                crash_fname = re.search("(\\S*\\w)\..*$", out).group(1)
                if crash_fname not in pending_set:
                    pending_set.add(crash_fname)
        return {'submitted': list(submitted_set),
                'pending': list(pending_set)}

    def get_crash(self):
        crash_info = self.fetch_crash_info()
        submitted = crash_info['submitted']
        pending = crash_info['pending']
        pending_dir = BASE_DIR + 'pending'
        processed = set()
        for pendi in set(pending):
            # Get pending dump and submit
            dmp = pendi + ".dmp"
            extra = pendi + ".extra"
            AdbWrapper.adb_pull('"' + pending_dir + "/" + dmp + '"',
                                dmp,
                                self.serial)
            AdbWrapper.adb_pull('"' + pending_dir + "/" + extra + '"',
                                extra,
                                self.serial)

            ret = cli([dmp])
            if ret:
                submitted.append(ret[0])
                AdbWrapper.adb_shell("rm \""
                                     + pending_dir
                                     + "/" + dmp + "\"")
                AdbWrapper.adb_shell("rm \""
                                     + pending_dir
                                     + "/" + extra + "\"")
                processed.add(pendi)
            os.remove(dmp)
            os.remove(extra)
        return {'crash_info': {
                'submitted': submitted,
                'pending': list(set(pending) - processed)}}


def read_extra(extra):
    data = {}
    with open(extra, "r") as f:
        for line in f.readlines():
            k, v = line.rstrip().split("=", 1)
            data[k] = v.replace("\\n", "\n")
    return data


def submit(dump, extra):
    data = read_extra(extra)
    if "ServerURL" in data:
        del data["ServerURL"]
    data['minidump_file'] = open(dump, "rb")
    datagen, headers = multipart_encode(data)
    request = urllib2.Request(SUBMIT_URL, datagen, headers)
    res = urllib2.urlopen(request)
    if res.getcode() != 200:
        sys.stderr.write("Error %d submitting dump %s" % (res.getcode(), dump))
        return None
    response = dict(l.split("=") for l in res.read().splitlines())
    if "CrashID" in response:
        url = REPORT_URL + response["CrashID"]
        return url
    return None


def cli(args):
    register_openers()
    ret = []
    for dump in args:
        if dump.endswith(".dmp") and os.path.isfile(dump):
            base, _ = os.path.splitext(dump)
            extra = base + ".extra"
            if not os.path.isfile(extra):
                sys.stderr.write("Skipping dump %s with missing .extra file"
                                 % dump)
                continue
            ret.append(submit(dump, extra))
    return ret


def main():
    serial_list = get_current_all_dev_serials()
    total_crash_num = 0
    for serial in serial_list:
        crash_info = CrashAgent(serial).get_crash()
        print crash_info
        total_crash_num += (len(crash_info['submitted'])
                            + len(crash_info['pending']))
    print("Total crash number = " + str(total_crash_num))


if __name__ == "__main__":
    main()
