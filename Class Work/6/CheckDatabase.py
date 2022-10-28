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
                        number_of_processes: int = multiprocessing.cpu_count(),
                        number_of_threads: int = os.cpu_count(),
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
               number_of_processes: int = multiprocessing.cpu_count(),
               number_of_threads: int = os.cpu_count(),
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
        name = "Thread" if mode == 0 else "Process"
        range_ = range(1, number_of_threads) if mode == 0 else range(1, number_of_processes)
        all_keys = [f"{name}-{i}" for i in range_]
        range_ = range(range_end // 2, range_end) if mode == 0 else range(range_end // 2, range_end)
        for name in all_keys:
            for i in range_:
                try:
                    if self.database[f"{name} {i}"] != i:
                        print(f"Error, '{f'{name} {i}'}' != {i}")
                        result = False
                except KeyError:
                    print(f"Error, missing the key '{f'{name} {i}'}'")
                    result = False
        stop = True
        animation_thread.join()
        return result

    def check_multiprocessing_and_threading(self,
                                            threading_range_end: int = 30,
                                            multiprocessing_range_end: int = 300,
                                            number_of_processes: int = multiprocessing.cpu_count(),
                                            number_of_threads: int = os.cpu_count(),
                                            max_reads_together: int = 10):
        # check threading
        start = datetime.datetime.now()
        print("Starting Check For Threading")
        result = self._check(0, threading_range_end,
                             number_of_threads=number_of_threads, max_reads_together=max_reads_together)
        print("-" * 64)
        if not result:
            print(" " * 28 + "FAILED")
        else:
            print(" " * 28 + "PASSED\n")
        total = number_of_threads * threading_range_end * 3
        total += total / 3 // 2
        print(f"Time Passed: {str(datetime.datetime.now() - start).split('.')[0]}, Total Operations: {int(total)}")
        # check multiprocessing
        start = datetime.datetime.now()
        print("Starting Check For Multiprocessing")
        result = self._check(1, multiprocessing_range_end,
                             number_of_processes=number_of_processes, max_reads_together=max_reads_together)
        print("-" * 64)
        if not result:
            print(" " * 28 + "FAILED")
        else:
            print(" " * 28 + "PASSED\n")
        total = number_of_processes * multiprocessing_range_end * 3
        total += total / 3 // 2
        print(f"Time Passed: {str(datetime.datetime.now() - start).split('.')[0]}, Total Operations: {int(total)}")


def main():
    database_checker = CheckDatabase()
    database_checker.check_multiprocessing_and_threading()


if __name__ == '__main__':
    main()
