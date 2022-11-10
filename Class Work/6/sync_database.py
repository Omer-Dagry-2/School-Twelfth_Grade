import os
import pickle
import threading
import multiprocessing

from typing import *
if "file_database.py" not in os.listdir():
    raise AssertionError("file_database.py file is missing.")
from file_database import FileDatabase


class SyncDatabase:
    def __init__(self, database: FileDatabase, mode: bool, max_reads_together: int = 10):
        """ mode: True -> multiprocessing, False -> threading """
        #
        # check that database is FileDatabase
        if not isinstance(database, FileDatabase):
            raise ValueError("the arg '__database' is an instance of FileDatabase.")
        # check that the mode is valid
        if not isinstance(mode, bool):
            raise ValueError("the arg 'mode' can be True or False, False for threads, True for processes.")
        # set params
        self.__database = database
        self.__mode = mode
        self.__max_reads_together = max_reads_together
        # set semaphores according to mode
        if self.__mode:
            self.__edit_lock = multiprocessing.Lock()
            self.__semaphore = multiprocessing.Semaphore(self.__max_reads_together)
        else:
            self.__edit_lock = threading.Lock()
            self.__semaphore = threading.Semaphore(self.__max_reads_together)

    def __setitem__(self, key: Hashable, val: Any) -> bool:
        """ Override & Add synchronization """
        # pickup edit lock
        self.__edit_lock.acquire()
        # acquire all the semaphore
        for _ in range(self.__max_reads_together):
            self.__semaphore.acquire()
        # here there is no one reading and or writing, so we can set key: val
        ok = self.__database[key] = val
        # release the edit lock
        self.__edit_lock.release()
        # release all the semaphore
        for _ in range(self.__max_reads_together):
            self.__semaphore.release()
        return ok

    def set_value(self, key: Hashable, val: Any) -> bool:
        """ Override & Add synchronization """
        return self.__database.set_value(key, val)

    def __getitem__(self, key: Hashable) -> Any:
        """ Override & Add synchronization """
        self.__semaphore.acquire()
        try:
            val = self.__database[key]
        # make sure that the lock is released even if KeyError raised
        except KeyError as key_error:
            self.__semaphore.release()
            raise key_error
        # release the lock
        self.__semaphore.release()
        return val

    def get_value(self, key: Hashable) -> Any:
        """ Override & Add synchronization """
        return self.__getitem__(key)

    def pop(self, key: Hashable) -> Any:
        """ Override & Add synchronization """
        # pickup edit lock
        self.__edit_lock.acquire()
        # acquire all the semaphore
        for _ in range(self.__max_reads_together):
            self.__semaphore.acquire()
        # here there is no one reading and or writing, so we can pop the key
        try:
            val = self.__database.pop(key)
        # make sure that the lock is released even if KeyError raised
        except KeyError as key_error:
            self.__edit_lock.release()
            # release all the semaphore
            for _ in range(self.__max_reads_together):
                self.__semaphore.release()
            raise key_error
        # release the lock
        self.__edit_lock.release()
        # release all the semaphore
        for _ in range(self.__max_reads_together):
            self.__semaphore.release()
        return val

    def delete_value(self, key: Hashable) -> Any:
        return self.pop(key)


# because each process has its own memory, this file will be imported
# by x processes, so the file name of the __database can't be the same
# for all the processes, or they will interfere with each other in the
# asserts because every action affects the file of the __database and there
# are x number of processes that will import this file simultaneously
file_name = f"####test####{os.getpid()}"
__ = FileDatabase(file_name)
try:
    _ = SyncDatabase(__, True)
    _["hello"] = 5  # check set_value & write & read
    assert _["hello"] == 5  # check get_value & read
    assert _.pop("hello") == 5  # check pop_value & write & read
    _["hi"] = 6
    _["bye"] = 5
    assert _["hi"] == 6 and _["bye"] == 5
    del _
    # check final result
    with open(file_name, "rb") as test_file:
        _ = pickle.load(test_file)
    assert _ == {"hi": 6, "bye": 5}
    del _, __
except BaseException as exception:
    raise exception
finally:
    os.remove(file_name)
    del file_name
