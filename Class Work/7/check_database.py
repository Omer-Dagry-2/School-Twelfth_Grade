from __future__ import annotations

import os
import time
import random
import datetime
import win32process

from typing import *
# my implementation of Threads and Processes using Windows api
from thread import Thread
from process import Process

if "sync_database.py" and "file_database.py" not in os.listdir():
    missing = [file for file in ["sync_database.py", "file_database.py"] if file not in os.listdir()]
    raise AssertionError(f"{', '.join(missing)} {'file is' if len(missing) == 1 else 'files are'} missing.")
from sync_database import SyncDatabase
from file_database import FileDatabase


stop_animation = False


class CheckDatabase:
    def __init__(self):
        self.__database: FileDatabase | None = None
        self.__can_start = False
        self.__started = False
        self.__threads_or_processes_pool: list[list[Process | Thread], ...] = []
        self.__animation_thread = None

    @staticmethod
    def animation(word: str = "Checking"):
        global stop_animation
        while not stop_animation:
            style = f"\x1b[{random.randint(0, 2)};{random.randint(31, 37)}m"
            for t in range(0, 5):
                print("\r" + style + word + "." * t, end="")
                time.sleep(0.3)
        print("\r" + "\x1b[0m", end="")  # delete animation row

    def start_animation(self, word: str = "Checking"):
        if self.__animation_thread is not None:
            raise Exception("Animation Already Started")
        global stop_animation
        stop_animation = False
        self.__animation_thread = Thread(target=self.animation, args=(word,))
        self.__animation_thread.start()

    def stop_animation(self):
        if self.__animation_thread is None:
            return
        elif not self.__animation_thread.is_alive():
            return
        global stop_animation
        stop_animation = True
        self.__animation_thread.join()
        self.__animation_thread = None

    @staticmethod
    def work(my_name: str, range_end: int, mode: str, sync_database: SyncDatabase):
        """ Work for workers (mode = "set" / "get" / "pop") """
        for i in range(range_end):
            key: str = f"{my_name} {i}"
            val: int = i
            if mode == "set":
                sync_database[key] = val
            elif mode == "get":
                if val != sync_database[key]:
                    print(f"Error the value of key '{key}' should be {val} but isn't")
            elif mode == "pop":
                if val != sync_database.pop(key):
                    print(f"Error the value of key '{key}' should be {val} but isn't")

    def create_database_and_workers(self, mode: bool, range_end: int, number_of_threads_or_processes: int,
                                    max_reads_together: int = 10):
        if self.__can_start or self.__started:
            raise Exception("Work Is Currently Running" if self.__started else "Already Created Workers")
        #
        self.__threads_or_processes_pool = [[], [], []]
        database = FileDatabase("databaseMultiprocessing" if mode else "databaseThreading", True, True)
        self.__database = database
        sync_database = SyncDatabase(database, mode, max_reads_together)
        sync_database["if we are not"] = "here at the end, the test failed"
        sync_database["remember to check"] = "if we are here"
        process_thread = Process if mode else Thread
        name = "Process" if mode else "Thread"
        for i in range(number_of_threads_or_processes):
            writer = process_thread(target=self.work, args=(f"{name}-{i}", range_end, "set", sync_database))
            reader = process_thread(target=self.work, args=(f"{name}-{i}", range_end, "get", sync_database))
            deleter = process_thread(target=self.work, args=(f"{name}-{i}", range_end, "pop", sync_database))
            self.__threads_or_processes_pool[0].append(writer)
            self.__threads_or_processes_pool[1].append(reader)
            self.__threads_or_processes_pool[2].append(deleter)
        self.__can_start = True  # workers created work can be started
        self.__started = False  # work haven't been started yet

    def start_work(self) -> bool:
        """ starts all processes / threads """
        if self.__can_start and self.__started:
            raise Exception("Can't start work twice")
        elif self.__can_start:
            self.__started = True
            self.__can_start = False
            pool, self.__threads_or_processes_pool = self.__threads_or_processes_pool, []
            writers = pool[0]
            for writer in writers:
                writer.start()
            while self.still_working(writers):
                time.sleep(0.5)
            #
            self.stop_animation()
            print("Done Writing.")
            self.start_animation()
            #
            readers = pool[1]
            for reader in readers:
                reader.start()
            while self.still_working(readers):
                time.sleep(0.5)
            #
            self.stop_animation()
            print("Done Reading.")
            self.start_animation()
            #
            deleter_list = pool[2]
            for deleter in deleter_list:
                deleter.start()
            while self.still_working(deleter_list):
                time.sleep(0.5)
            #
            self.stop_animation()
            print("Done Deleting.")
            self.start_animation()
            #
            self.__threads_or_processes_pool = pool
            return True
        else:
            raise Exception("Please call `create_database_and_workers()` before calling `start_work()`")

    def still_working(self, pool: list[Process | Thread]) -> bool:
        """ if there are still threads/processes alive -> True, else -> False"""
        for p_t in pool:
            if p_t.is_alive():
                return True
            else:
                pool.remove(p_t)
        else:
            self.__can_start = False
            self.__started = False
            return False

    def _check(self, mode: bool, range_end: int, number_of_threads_or_processes: int, max_reads_together: int = 10):
        # animation
        self.start_animation()
        # create database and workers
        self.create_database_and_workers(mode, range_end, number_of_threads_or_processes, max_reads_together)
        # start workers
        self.start_work()
        # stop the animation
        self.stop_animation()
        # check the result
        if self.__database.get_database() == \
                {"if we are not": "here at the end, the test failed", "remember to check": "if we are here"}:
            return True
        return False

    def _check_threading(self, threading_range, number_of_threads, max_reads_together):
        start = datetime.datetime.now()
        print(f"Starting Check For Threading (on {number_of_threads} threads)")
        result = self._check(False, threading_range, number_of_threads, max_reads_together)
        total = number_of_threads * threading_range * 3 if result else "Unknown, Failed."
        print(f"Time Passed: {str(datetime.datetime.now() - start).split('.')[0]}, Total Operations: {total}")
        print(f" {'PASSED' if result else 'FAILED'} ".center(64, "-"))

    def _check_multiprocessing(self, multiprocessing_range, number_of_processes, max_reads_together):
        start = datetime.datetime.now()
        print(f"Starting Check For Multiprocessing (on {number_of_processes} processes)")
        result = self._check(True, multiprocessing_range, number_of_processes, max_reads_together)
        total = number_of_processes * multiprocessing_range * 3 if result else "Unknown, Failed."
        print(f"Time Passed: {str(datetime.datetime.now() - start).split('.')[0]}, Total Operations: {total}")
        print(f" {'PASSED' if result else 'FAILED'} ".center(64, "-"))

    def check_multiprocessing_and_threading(self, threading_range: int = 300, multiprocessing_range: int = 300,
                                            number_of_processes: int = os.cpu_count() * 2,
                                            number_of_threads: int = os.cpu_count() * 10,
                                            max_reads_together: int = 10):
        # check threading
        self._check_threading(threading_range, number_of_threads, max_reads_together)
        # check multiprocessing
        self._check_multiprocessing(multiprocessing_range, number_of_processes, max_reads_together)


def main():
    database_checker = CheckDatabase()
    database_checker.check_multiprocessing_and_threading(number_of_threads=5, number_of_processes=5)


if __name__ == '__main__':
    main()
