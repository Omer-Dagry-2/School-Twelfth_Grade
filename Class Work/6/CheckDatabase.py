import os
import random
import time
import datetime
import threading
import multiprocessing

if "SynchronizedDatabase.py" not in os.listdir():
    raise AssertionError("SynchronizedDatabase.py file is missing.")
from SynchronizedDatabase import SynchronizedDatabase


stop = False


class CheckDatabase:
    def __init__(self):
        self.database = None

    @staticmethod
    def animation(word: str = "Checking"):
        global stop
        while not stop:
            for t in range(0, 5):
                style = f"\x1b[{random.randint(0, 2)};{random.randint(31, 37)}m"
                print("\r" + style + word + "." * t, end="")
                time.sleep(0.2)
        print("\r" + "\x1b[0m", end="")  # delete animation row

    def create_database(self, mode: int, range_end: int,
                        number_of_processes: int = multiprocessing.cpu_count() * 2,
                        number_of_threads: int = multiprocessing.cpu_count() * 10,
                        max_reads_together: int = 10):
        synchronized_database = SynchronizedDatabase(mode=mode,
                                                     number_of_processes=number_of_processes,
                                                     number_of_threads=number_of_threads,
                                                     max_reads_together=max_reads_together)
        synchronized_database.create_workers(range_end)
        synchronized_database.start_work()
        while synchronized_database.still_working():
            time.sleep(2)
        self.database = synchronized_database.get_database()

    def _check(self, mode: int, range_end: int,
               number_of_processes: int = multiprocessing.cpu_count() * 2,
               number_of_threads: int = multiprocessing.cpu_count() * 10,
               max_reads_together: int = 10):
        global stop
        stop = False
        animation_thread = threading.Thread(target=self.animation, daemon=True)
        animation_thread.start()
        result = True
        self.create_database(mode, range_end,
                             number_of_processes=number_of_processes,
                             number_of_threads=number_of_threads,
                             max_reads_together=max_reads_together)
        stop = True
        animation_thread.join()
        #
        range_ = range(number_of_threads) if mode == 0 else range(number_of_processes)
        all_keys = [f"{'Thread' if mode == 0 else 'Process'}-{i // 3}" for i in range_]
        # the `work` function in SynchronizedDatabase class gives work like this:
        # first process or thread gets SET work
        # second gets GET work
        # third gets POP work
        # every 3 processes / threads work on the same variables, so if the number_of_processes/threads % 3 == 0
        # the database will be empty at the end
        #
        #                                   ** so 2 options **
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
        if (mode == 0 and number_of_threads % 3 == 0) or (mode == 1 and number_of_processes % 3 == 0):
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

    def check_multiprocessing_and_threading(self,
                                            threading_range_end: int = 30,
                                            multiprocessing_range_end: int = 300,
                                            number_of_processes: int = multiprocessing.cpu_count() * 2,
                                            number_of_threads: int = multiprocessing.cpu_count() * 10,
                                            max_reads_together: int = 10):
        # check threading
        start = datetime.datetime.now()
        print(f"Starting Check For Threading (on {number_of_threads} threads)")
        result = self._check(0, threading_range_end,
                             number_of_threads=number_of_threads, max_reads_together=max_reads_together)
        total = number_of_threads * threading_range_end if result else "Unknown, Failed."
        print(f"Time Passed: {str(datetime.datetime.now() - start).split('.')[0]}, Total Operations: {total}")
        if not result:
            print(" FAILED ".center(64, "-"))
        else:
            print(" PASSED ".center(64, "-"))
        # check multiprocessing
        start = datetime.datetime.now()
        print(f"Starting Check For Multiprocessing (on {number_of_processes} processes)")
        result = self._check(1, multiprocessing_range_end,
                             number_of_processes=number_of_processes, max_reads_together=max_reads_together)
        total = number_of_processes * multiprocessing_range_end if result else "Unknown, Failed."
        print(f"Time Passed: {str(datetime.datetime.now() - start).split('.')[0]}, Total Operations: {total}")
        if not result:
            print(" FAILED ".center(64, "-"))
        else:
            print(" PASSED ".center(64, "-"))


def main():
    database_checker = CheckDatabase()
    database_checker.check_multiprocessing_and_threading()


if __name__ == '__main__':
    main()
