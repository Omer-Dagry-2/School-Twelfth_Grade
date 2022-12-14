import os
import pickle
import win32file

from typing import *
if "database.py" not in os.listdir():
    raise AssertionError("database.py file is missing.")
from database import Database


class FileDatabase(Database):
    def __init__(self, database_file_name: str, ignore_existing: bool = False, clear_database: bool = False,
                 delete_file_when_object_is_deleted: bool = False):
        super().__init__()
        if os.path.isfile(database_file_name):
            if not ignore_existing:
                raise ValueError(f"The File '{database_file_name}' Already Exists.")
            if clear_database:
                os.remove(database_file_name)
        self.__database_file_name = database_file_name
        self.delete_file_when_object_is_deleted = delete_file_when_object_is_deleted
        # create the file
        file_handle = win32file.CreateFileW(self.__database_file_name, win32file.GENERIC_WRITE,
                                            win32file.FILE_SHARE_WRITE | win32file.FILE_SHARE_READ,
                                            None, win32file.OPEN_ALWAYS, 0)
        self.close_database_file(file_handle)

    def write_database(self, read_after: bool = True):
        """ Write `self.__database` to a file using pickle """
        # open the file, and don't allow others to read write or delete
        file_handle = win32file.CreateFileW(self.__database_file_name, win32file.GENERIC_WRITE,
                                            win32file.FILE_SHARE_WRITE | win32file.FILE_SHARE_READ,
                                            None, win32file.OPEN_ALWAYS, 0)
        return_code, number_of_bytes_writen = win32file.WriteFile(file_handle,
                                                                  pickle.dumps(super().get_database()))
        if return_code != 0:
            raise ValueError(f"Failed to write database to File Database, Return Code {return_code}.")
        self.close_database_file(file_handle)
        if read_after:
            self.read_database()

    def read_database(self):
        """ Read __database file with pickle and set `self.__database` """
        # open the file, and allow others to open it to read
        file_handle = win32file.CreateFileW(self.__database_file_name, win32file.GENERIC_READ,
                                            win32file.FILE_SHARE_WRITE | win32file.FILE_SHARE_READ,
                                            None, win32file.OPEN_ALWAYS, 0)
        return_code, file_data = win32file.ReadFile(file_handle, os.path.getsize(self.__database_file_name))
        if return_code != 0:
            raise ValueError(f"Failed to read the File Database. Return Code: {return_code}.")
        self.close_database_file(file_handle)
        try:
            dic = pickle.loads(file_data)
        except EOFError:  # file is empty
            dic = {}
        ok = super().set_database(dic)
        while not ok:
            ok = super().set_database(dic)

    def set_database(self, dic: dict) -> bool:
        """ Override & write the __database after setting it """
        ok = super().set_database(dic)
        if ok:
            self.write_database()
        return ok

    def get_database(self) -> dict:
        """ Override & read from __database before returning the __database"""
        self.read_database()
        return super().get_database()

    def __setitem__(self, key: Hashable, val: Any) -> bool:
        """ Override & add read & write __database with pickle """
        self.read_database()
        ok = super().__setitem__(key, val)
        self.write_database()
        return ok

    def set_value(self, key: Hashable, val: Any) -> bool:
        """ Override & add read & write __database with pickle """
        return self.__setitem__(key, val)

    def __getitem__(self, key: Hashable) -> Any:
        """ Override & add read __database with pickle """
        self.read_database()
        return super().__getitem__(key)

    def get_value(self, key: Hashable) -> Any:
        """ Override & add read __database with pickle """
        return self.__getitem__(key)

    def pop(self, key: Hashable) -> Any:
        """ Override & add read & write __database with pickle """
        self.read_database()
        val = super().pop(key)
        self.write_database()
        return val

    def delete_value(self, key: Hashable) -> Any:
        """ Override & add read & write __database with pickle """
        return self.pop(key)

    @staticmethod
    def close_database_file(file_handle):
        if file_handle is not None:
            win32file.CloseHandle(file_handle)

    def __del__(self):
        if self.delete_file_when_object_is_deleted:
            os.remove(self.__database_file_name)


# because each process has its own memory, this file will be imported
# by x processes, so the file name of the __database can't be the same
# for all the processes, or they will interfere with each other in the
# asserts because every action affects the file of the __database and there
# are x number of processes that will import this file simultaneously
file_name = f"####test####{os.getpid()}"
try:
    _ = FileDatabase(database_file_name=file_name)
    _["hello"] = 5  # check set_value & write & read
    assert _["hello"] == 5  # check get_value & read
    assert _.pop("hello") == 5  # check pop_value & write & read
    _.set_database({"hi": 6, "bye": 5})  # check set_database & write
    assert _.get_database() == {"hi": 6, "bye": 5}  # check get_database & read
    del _
    # check final result
    with open(file_name, "rb") as test_file:
        _ = pickle.load(test_file)
    assert _ == {"hi": 6, "bye": 5}
    del _
except BaseException as exception:
    raise exception
finally:
    os.remove(file_name)
    del file_name
