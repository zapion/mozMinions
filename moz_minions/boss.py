#!/usr/bin/python
import os
import json
import time
from apscheduler.schedulers.background import BackgroundScheduler
# from apscheduler.triggers.inteval import IntervalTrigger
from minions import ShellMinion


class Boss(object):
    default_path = None
    workers = []

    def __init__(self):
        '''
        local path for load config
        '''
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        if self.default_path:
            self.load(self.default_path)

    def load_dir(self, folder):
        (dirpath, dirnames, filenames) = os.walk(folder).next()
        for fn in filenames:
            self.load(os.path.join(dirpath, fn))

    def load(self, fp):
        '''
        given a file
        TBI: directory
        '''
        with open(fp) as in_data:
            data = json.load(in_data)
            minion = ShellMinion(**data)
            self.workers.append(minion)
            self.scheduler.add_job(minion.collect, 'interval',
                                   name=minion.name+'_'+minion.serial,
                                   seconds=30
                                   )

    def list(self):
        '''
        to list all configs loaded
        format: [squence number] [minion name] [config_path] [status]
        '''
        for worker in self.workers:
            print(str(worker))

    def remove(self, sn):
        '''
        given an SN, stop running instance if possible
        TODO: remove it from the list
        '''
        self.scheduler.remove_job(sn)

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

    def stop(self, sn):
        '''
        simply stop running instance but not remove config
        TODO: should have timeout if stop failed
        '''
        self.scheduler.stop(sn)

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
    # b = Boss()
    # b.load('./e481d81e.json')
    # b.load('./conf/7ed3caf6.json')
    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

    try:
        # This is here to simulate application activity (which keeps the main
        # thread alive).
        while True:
            time.sleep(5)
    except (KeyboardInterrupt, SystemExit):
            pass

if __name__ == '__main__':
    main()
