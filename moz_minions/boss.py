#!/usr/bin/python
import os
import sys
import json
import time
import argparse
from apscheduler.schedulers.background import BackgroundScheduler
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from minions import ShellMinion


class JsonHandler(PatternMatchingEventHandler):
    def set_handler(self, oncreated=None, onmodified=None, ondeleted=None):
        self.create_handler = oncreated
        self.modify_handler = onmodified
        self.delete_handler = ondeleted

    def on_created(self, event):
        self.create_handler(event.src_path)

    def on_modified(self, event):
        self.modify_handler(event.src_path)

    def on_deleted(self, event):
        self.delete_handler(event.src_path)


class Boss(object):
    workers = {}
    dirpath = '.'
    output = None

    def __init__(self, dirpath='.', output='output'):
        '''
        local path for load config
        '''
        if os.path.isdir(dirpath):
            self.dirpath = dirpath
        else:
            print(dirpath + " is invalid, use default path instead")
        self.output = output
        if not os.path.isdir(output):
            print("target directory " + output + " doesn't exist, creating..")
            os.makedirs(output)

        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

        self.load_dir(dirpath)

        event_handler = JsonHandler(patterns=["*.json"],
                                    ignore_directories=True)
        event_handler.set_handler(oncreated=self.load,
                                  onmodified=self.load,
                                  ondeleted=self.remove)
        observer = Observer()
        observer.schedule(event_handler, self.dirpath, recursive=True)
        observer.start()

    def load_dir(self, folder):
        (dirpath, dirnames, filenames) = os.walk(folder).next()
        for fname in filenames:
            if 'json' in fname[-4:]:
                self.load(os.path.join(dirpath, fname))

    def load(self, fp):
        '''
        given a json file, load and create a task run regularly
        '''
        # for debugging
        print(fp + " was loaded!")
        with open(fp) as in_data:
            try:
                data = json.load(in_data)
            except ValueError as e:
                print(fp + " loaded failed: " + e.message)
                return None
            interval = 30
            if 'interval' in data:
                interval = data['interval']
            if fp in self.workers:
                minion = self.workers[fp]
                # //memo: Interval can't be modified
                self.scheduler.modify_job(job_id=fp,
                                          func=minion.collect,
                                          name=minion.name+'_'+minion.serial
                                          )

            else:
                if self.output:
                    output = data['output']
                    if 'dirpath' in output:
                        output['dirpath'] = os.path.join(self.output,
                                                         output['dirpath'])
                    else:
                        output['dirpath'] = self.output
                minion = ShellMinion(**data)
                self.workers[fp] = minion
                self.scheduler.add_job(minion.collect, 'interval',
                                       id=fp,
                                       name=minion.name+'_'+minion.serial,
                                       seconds=interval
                                       )
            return minion
        return None

    def list(self):
        '''
        to list all configs loaded
        format: [squence number] [minion name] [config_path] [status]
        '''
        for (fp, worker) in self.workers:
            print("path=" + fp + "," + str(worker) + ";")

    def remove(self, fp):
        '''
        given file path, stop running instance if possible
        '''
        if fp in self.workers:
            self.scheduler.remove_job(job_id=fp)
            del self.workers[fp]
            return True
        return False

    def remove_advanced(self):
        '''
        TODO:
        1. remove by start, end
        2. by directory(?)
        '''
        pass

    def unload_all(self):
        '''
        stop all running instances
        '''
        self.scheduler.shutdown()

    def pause(self, fp):
        '''
        simply stop running instance but not remove config
        TODO: should have timeout if stop failed
        '''
        self.scheduler.pause(job_id=fp)

    def resume(self, sn):
        # not sure we can do this
        pass

    def __del__(self):
        self.unload_all()

    def get_config(self):
        conf = {}
        return conf

    def _wake(self):
        '''
        For periodical minions, waking them according to timing
        '''
        pass


def main():
    # TODO: Add test for loading files
    # --output for storing monitoring data if using file
    parser = argparse.ArgumentParser(description="Boss monitoring")
    parser.add_argument('--dirpath', help="Boss will monitor this directory",
                        default='.')
    parser.add_argument('--output',
                        help="storing monitoring data if using file",
                        default='output')
    options = parser.parse_args(sys.argv[1:])
    b = Boss(**options.__dict__)
    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

    try:
        # This is here to simulate application activity (which keeps the main
        # thread alive).
        while True:
            time.sleep(5)
    except (KeyboardInterrupt, SystemExit):
            del b

if __name__ == '__main__':
    main()
