import os
import pickle

from typing import *
if "BaseDatabase.py" not in os.listdir():
    raise AssertionError("BaseDatabase.py file is missing.")
from BaseDatabase import BaseDatabase


class Database(BaseDatabase):
    def __init__(self, database_file_name: str = "database"):
        super().__init__()
        self.database_file_name = database_file_name
        with open(self.database_file_name, "wb") as database_file:
            database_file.write(b"")

    def write_database(self, read_after: bool = True):
        """ Write `self.database` to a file using pickle """
        with open(self.database_file_name, "wb") as database_file:
            data = pickle.dumps(self.database)
            database_file.write(data)
        if read_after:
            self.read_database()

    def read_database(self):
        """ Read database file with pickle and set `self.database` """
        with open(self.database_file_name, "rb") as database_file:
            try:
                dic = pickle.load(database_file)
            except EOFError:  # file is empty
                dic = {}
        ok = super().set_database(dic)  # don't use `self.set_database`, RecursionError
        while not ok:
            ok = super().set_database(dic)

    def set_database(self, dic: dict) -> bool:
        """ Override & write the database after setting it """
        ok = super().set_database(dic)
        if ok:
            self.write_database()
        return ok

    def get_database(self) -> dict:
        """ Override & read from database before returning the database"""
        self.read_database()
        return super().get_database()

    def __setitem__(self, key: Hashable, val: Any) -> bool:
        """ Override & add read & write database with pickle """
        self.read_database()
        ok = super().__setitem__(key, val)
        self.write_database()
        return ok

    def set_value(self, key: Hashable, val: Any) -> bool:
        """ Override & add read & write database with pickle """
        return self.__setitem__(key, val)

    def pop(self, key: Hashable) -> Any:
        """ Override & add read & write database with pickle """
        self.read_database()
        val = super().pop(key)
        self.write_database()
        return val

    def __getitem__(self, key: Hashable) -> Any:
        """ Override & add read database with pickle """
        self.read_database()
        return super().__getitem__(key)

    def get_value(self, key: Hashable) -> Any:
        """ Override & add read database with pickle """
        return self.__getitem__(key)


if __name__ == '__main__':
    _ = Database(database_file_name="####test####")
    _["hello"] = 5  # check set_value & write & read
    if _["hello"] != 5:  # check get_value & read
        raise AssertionError
    if _.pop("hello") != 5:  # check pop_value & write & read
        raise AssertionError
    _.set_database({"hi": 6, "bye": 5})  # check set_database & write
    if _.get_database() != {"hi": 6, "bye": 5}:  # check get_database & read
        raise AssertionError
    del _
    # check final result
    with open("####test####", "rb") as test_file:
        _ = pickle.load(test_file)
    if _ != {"hi": 6, "bye": 5}:
        raise AssertionError
    del test_file, _
    os.remove("####test####")
