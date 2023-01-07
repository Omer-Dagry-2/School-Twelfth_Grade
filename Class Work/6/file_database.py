import os
import pickle

from typing import *
if "database.py" not in os.listdir():
    raise AssertionError("database.py file is missing.")
from database import Database


class FileDatabase(Database):
    def __init__(self, database_file_name: str, ignore_existing: bool = False, clear_database: bool = False):
        super().__init__()
        if os.path.isfile(database_file_name) and not ignore_existing:
            raise ValueError(f"The File '{database_file_name}' Already Exists.")
        self.__database_file_name = database_file_name
        with open(self.__database_file_name, "wb" if clear_database else "ab") as db:  # create the database file
            if clear_database:  # clear database if clear_database
                db.write(b"")

    def write_database(self, read_after: bool = True):
        """ Write `self.__database` to a file using pickle """
        with open(self.__database_file_name, "wb") as database_file:
            data = pickle.dumps(super().get_database())
            database_file.write(data)
        if read_after:
            self.read_database()

    def read_database(self):
        """ Read __database file with pickle and set `self.__database` """
        with open(self.__database_file_name, "rb") as database_file:
            try:
                dic = pickle.load(database_file)
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
