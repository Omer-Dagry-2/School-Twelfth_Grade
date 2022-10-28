import os
import time
import threading
import multiprocessing

from typing import *
if "Database.py" not in os.listdir():
    raise AssertionError("Database.py file is missing.")
from Database import Database


class SynchronizedDatabase(Database):
    def __init__(self,
                 mode: int = 1,
                 number_of_processes: int = multiprocessing.cpu_count(),
                 number_of_threads: int = multiprocessing.cpu_count(),
                 max_reads_together: int = 10):
        #
        # check that the mode is valid
        if mode not in [0, 1]:
            raise ValueError("the arg 'mode' can be 0 or 1, 0 for threads, 1 for processes.")
        # call super()
        super().__init__()
        # set params
        self.mode = mode
        self.number_of_processes = number_of_processes
        self.number_of_threads = number_of_threads
        self.max_reads_together = max_reads_together
        self.can_start = False
        self.started = False
        self.threads_or_processes_pool: list[Union[multiprocessing.Process, threading.Thread]] = []
        # set semaphores according to mode
        if mode == 1:
            self.edit_and_read_lock = multiprocessing.Semaphore(1)
            self.semaphore = multiprocessing.Semaphore(self.max_reads_together)
        else:
            self.edit_and_read_lock = threading.Semaphore(1)
            self.semaphore = threading.Semaphore(self.max_reads_together)

    def get_semaphore_value(self) -> int:
        """ Get the value of the semaphore lock that limit the amount of reads at a time"""
        if self.mode == 1:
            return self.semaphore.get_value()
        else:
            return self.semaphore._value

    def get_edit_and_read_lock_value(self) -> int:
        """ Get the value of the semaphore lock that prevent multiple writes at a time """
        if self.mode == 1:
            return self.edit_and_read_lock.get_value()
        else:
            return self.edit_and_read_lock._value

    def __setitem__(self, key: Hashable, val: Any) -> bool:
        """ Override & Add synchronization """
        # pickup edit and read lock
        self.edit_and_read_lock.acquire()
        # wait until every one who was already reading is done
        while self.get_semaphore_value() != self.max_reads_together:
            time.sleep(0.1)  # prevent high cpu usage
        # here there is no one reading and or writing, so we can set key: val
        ok = super().__setitem__(key, val)
        # release the lock
        self.edit_and_read_lock.release()
        return ok

    def set_value(self, key: Hashable, val: Any) -> bool:
        """ Override & Add synchronization """
        return super().set_value(key, val)

    def __getitem__(self, key: Hashable) -> Any:
        """ Override & Add synchronization """
        # wait until no one is editing the dictionary
        while self.get_edit_and_read_lock_value() != 1:
            time.sleep(0.1)  # prevent high cpu usage
        self.semaphore.acquire()
        # print(f"get {key}   {self.get_edit_and_read_lock_value() == 1}")
        val = super().__getitem__(key)
        # release the lock
        self.semaphore.release()
        return val

    def get_value(self, key: Hashable) -> Any:
        """ Override & Add synchronization """
        return super().__getitem__(key)

    def pop(self, key: Hashable) -> Any:
        """ Override & Add synchronization """
        # pickup edit and read lock
        self.edit_and_read_lock.acquire()
        # wait until every one who was already reading is done
        while self.get_semaphore_value() != self.max_reads_together:
            time.sleep(0.1)  # prevent high cpu usage
        # here there is no one reading and or writing, so we can set key: val
        val = super().pop(key)
        # release the lock
        self.edit_and_read_lock.release()
        return val

    def work(self, my_name: str, range_end: int):
        """ Work for workers """
        # print(f"setting '{range_end}' values")
        for i in range(range_end):  # sets & gets
            key: str = f"{my_name} {i}"
            val: int = i
            self[key] = val  # set
            if not self[key] == val:  # get
                print(f"Error {key} {val}")
        # print(f"'{range_end}' values are set")
        # print(f"getting {range_end} values")
        for i in range(range_end):  # gets
            key: str = f"{my_name} {i}"
            val: int = i
            if not self[key] == val:  # get
                print(f"Error {key} {val}")
        # print(f"got '{range_end}' values")
        # print(f"popping {range_end} values")
        for i in range(range_end // 2):  # pops
            key: str = f"{my_name} {i}"
            val: int = i
            if self.pop(key) != val:  # pop
                print(f"Error {key} != {val}")
        # print(f"popped '{range_end}' values")

    def create_workers(self, range_end=300) -> bool:
        """ Create All The Workers """
        if not self.started and not self.can_start:
            pool = []
            init_thread_or_process = threading.Thread if self.mode == 0 else multiprocessing.Process
            range_ = range(self.number_of_threads) if self.mode == 0 else range(self.number_of_processes)
            name = "Thread" if self.mode == 0 else "Process"
            for i in range_:
                thread_or_process = init_thread_or_process(target=self.work,
                                                           args=(f"{name}-{i + 1}", range_end), daemon=True)
                self.threads_or_processes_pool.append(thread_or_process)
                pool.append(thread_or_process)
            self.can_start = True
            return True
        else:
            raise Exception("Already created workers")

    def start_work(self) -> bool:
        if self.can_start and self.started:
            raise Exception("Can't start work twice")
        elif self.can_start:
            pool, self.threads_or_processes_pool = self.threads_or_processes_pool, []
            for threads_or_processes in pool:
                threads_or_processes.start()
            self.threads_or_processes_pool = pool
            self.started = True
            return True
        else:
            raise Exception("Please call `create_workers()` before calling `start_work()`")

    def still_working(self) -> bool:
        """ if there are still threads/processes alive -> True, else -> False"""
        for thread_or_process in self.threads_or_processes_pool:
            if thread_or_process.is_alive():
                return True
            else:
                self.threads_or_processes_pool.remove(thread_or_process)
        else:
            return False
