from __future__ import annotations

import os
import time
import random
import datetime
import threading
import multiprocessing

if "sync_database.py" and "file_database.py" not in os.listdir():
    missing = [file for file in ["sync_database.py", "file_database.py"] if file not in os.listdir()]
    raise AssertionError(f"{', '.join(missing)} {'file is' if len(missing) == 1 else 'files are'} missing.")
from sync_database import SyncDatabase
from file_database import FileDatabase


stop_animation = False


class CheckDatabase:
    def __init__(self):
        self.database = None
        self.can_start = False
        self.started = False
        self.threads_or_processes_pool: list[multiprocessing.Process | threading.Thread] = []

    @staticmethod
    def animation(word: str = "Checking"):
        global stop_animation
        while not stop_animation:
            style = f"\x1b[{random.randint(0, 2)};{random.randint(31, 37)}m"
            for t in range(0, 5):
                print("\r" + style + word + "." * t, end="")
                time.sleep(0.1)
        print("\r" + "\x1b[0m", end="")  # delete animation row

    @staticmethod
    def work(my_name: str, range_end: int, mode: str, sync_database: SyncDatabase):
        """ Work for workers (mode = "set" / "get" / "pop") """
        for i in range(range_end):
            key: str = f"{my_name} {i}"
            val: int = i
            if mode == "set":
                sync_database[key] = val  # set
            elif mode == "get":
                try:
                    if val != sync_database[key]:
                        print(f"Error the value of key '{key}' should be {val} but isn't")
                except KeyError:  # if key isn't set yet or key already have been popped
                    pass
            elif mode == "pop":
                while True:
                    try:
                        if val != sync_database.pop(key):
                            print(f"Error the value of key '{key}' should be {val} but isn't")
                        break
                    except KeyError:  # if key isn't set yet
                        pass
                    time.sleep(0.1)  # prevent high cpu usage

    def create_database_and_workers(self, mode: bool, range_end: int,
                                    number_of_processes: int = multiprocessing.cpu_count() * 2,
                                    number_of_threads: int = multiprocessing.cpu_count() * 10,
                                    max_reads_together: int = 10):
        if self.can_start or self.started:
            raise Exception("Work Is Currently Running" if self.started else "Already Created Workers")
        #
        self.threads_or_processes_pool = []
        database = FileDatabase("databaseMultiprocessing" if mode else "databaseThreading")
        sync_database = SyncDatabase(database, mode, max_reads_together)
        range_ = range(number_of_processes) if mode else range(number_of_threads)
        process_thread = multiprocessing.Process if mode else threading.Thread
        name = "Process" if mode else "Thread"
        modes = ["set", "get", "pop"]
        for i in range_:
            thread_or_process = process_thread(target=self.work,
                                               args=(
                                                   f"{name}-{i // 3}",
                                                   range_end,
                                                   modes[i % 3],
                                                   sync_database,
                                               ),
                                               daemon=True)
            self.threads_or_processes_pool.append(thread_or_process)
        self.can_start = True  # workers created work can be started
        self.started = False  # work haven't been started yet

    def start_work(self) -> bool:
        """ starts all processes / threads """
        if self.can_start and self.started:
            raise Exception("Can't start work twice")
        elif self.can_start:
            pool, self.threads_or_processes_pool = self.threads_or_processes_pool, []
            for threads_or_processes in pool:
                threads_or_processes.start()
            self.threads_or_processes_pool = pool
            self.started = True
            self.can_start = False
            return True
        else:
            raise Exception("Please call `create_database_and_workers()` before calling `start_work()`")

    def still_working(self) -> bool:
        """ if there are still threads/processes alive -> True, else -> False"""
        for p_t in self.threads_or_processes_pool:
            if p_t.is_alive():
                return True
            else:
                self.threads_or_processes_pool.remove(p_t)
        else:
            self.can_start = False
            self.started = False
            return False

    def _check(self, mode: bool, range_end: int, max_reads_together: int = 10,
               number_of_processes: int = multiprocessing.cpu_count() * 2,
               number_of_threads: int = multiprocessing.cpu_count() * 10):
        # animation
        global stop_animation
        stop_animation = False
        animation_thread = threading.Thread(target=self.animation, daemon=True)
        animation_thread.start()
        # create database and workers
        result = True
        self.create_database_and_workers(mode, range_end, number_of_processes, number_of_threads, max_reads_together)
        # start workers
        self.start_work()
        # wait for the work to finish
        while self.still_working():
            time.sleep(1.5)  # prevent high cpu usage
        # stop the animation
        stop_animation = True
        animation_thread.join()
        # check the result
        range_ = range(number_of_threads) if mode == 0 else range(number_of_processes)
        all_keys = [f"{'Thread' if mode == 0 else 'Process'}-{i // 3}" for i in range_]
        # the `work` function in SynchronizedDatabase class gives work like this:
        # first process or thread gets SET work
        # second gets GET work
        # third gets POP work
        # every 3 processes / threads work on the same variables, so if the number_of_processes/threads % 3 == 0
        # the database will be empty at the end, so there are 2 options
        # **** OPTION 1 ****
        # if the number_of_threads/processes that was open % 3 == 0, self.database should be equal to {}
        # **** OPTION 2 ****
        # if the number_of_threads/processes % 3 != 0, (== 1 or == 2) which means
        # that if the result of number_of_threads/processes % 3 == 1
        # there will be a thread/process that will do SET work and ** no one will delete his work **.
        # or if the result == 2 there will be a processes/thread that will do SET work and another
        # process/thread that will do GET work but still there will be ** no one to POP (delete) the work **.
        # so if number_of_threads/processes % 3 != 0 the work of the last process/thread that did SET work should stay.
        # self.database = {the work of the process that didn't have 2 more "teammates"}
        if (not mode and number_of_threads % 3 == 0) or (mode and number_of_processes % 3 == 0):
            if self.database == {}:
                result = True
        else:
            name = all_keys[-1]
            for i in range(range_end):
                try:
                    if self.database[f"{name} {i}"] != i:
                        print(f"Error, '{f'{name} {i}'}' != {i}")
                        result = False
                except KeyError:
                    print(f"Error, missing the key '{f'{name} {i}'}'")
                    result = False
        return result

    def check_multiprocessing_and_threading(self, threading_range: int = 300,
                                            multiprocessing_range: int = 3000,
                                            number_of_processes: int = multiprocessing.cpu_count() * 2,
                                            number_of_threads: int = multiprocessing.cpu_count() * 10,
                                            max_reads_together: int = 10):
        # check threading
        start = datetime.datetime.now()
        print(f"Starting Check For Threading (on {number_of_threads} threads)")
        result = self._check(False, threading_range, max_reads_together, number_of_threads=number_of_threads)
        total = number_of_threads * threading_range if result else "Unknown, Failed."
        print(f"Time Passed: {str(datetime.datetime.now() - start).split('.')[0]}, Total Operations: {total}")
        print(f" {'PASSED' if result else 'FAILED'} ".center(64, "-"))
        # check multiprocessing
        start = datetime.datetime.now()
        print(f"Starting Check For Multiprocessing (on {number_of_processes} processes)")
        result = self._check(True, multiprocessing_range, max_reads_together, number_of_processes=number_of_processes)
        total = number_of_processes * multiprocessing_range if result else "Unknown, Failed."
        print(f"Time Passed: {str(datetime.datetime.now() - start).split('.')[0]}, Total Operations: {total}")
        print(f" {'PASSED' if result else 'FAILED'} ".center(64, "-"))


def main():
    database_checker = CheckDatabase()
    database_checker.check_multiprocessing_and_threading()


if __name__ == '__main__':
    main()
