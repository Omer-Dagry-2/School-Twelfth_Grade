from typing import *


class BaseDatabase:
    def __init__(self):
        self.database = {}

    def set_database(self, dic: dict) -> bool:
        """ set self.database """
        self.database = dic
        return True

    def get_database(self) -> dict:
        """ get self.database """
        return self.database

    def __setitem__(self, key: Hashable, val: Any) -> bool:
        """ add key: val """
        # print("set")
        if not isinstance(key, Hashable):
            key_type = str(type(key)).split("'")[1]
            raise TypeError(f"{key} (type: {key_type}) can't be a key in "
                            f"the database, only hashable types can be keys.")
        self.database[key] = val
        return True

    def set_value(self, key: Hashable, val: Any) -> bool:
        """ add key: val """
        return self.__setitem__(key, val)

    def __getitem__(self, key: Hashable) -> Any:
        # print("get")
        """ get the val of key """
        if key in self.database.keys():
            val = self.database[key]
            return val
        else:
            raise KeyError(f"{key} isn't a key in the database.")

    def get_value(self, key: Hashable) -> Any:
        """ get the val of key """
        return self.__getitem__(key)

    def pop(self, key: Hashable) -> Any:
        # print("pop")
        """ remove key and self.database[key] value """
        if key in self.database.keys():
            return self.database.pop(key)
        else:
            raise KeyError(f"{key} isn't a key in the database.")


_ = BaseDatabase()
_["hello"] = 5  # check set_value
assert _["hello"] == 5  # check get_value
assert _.pop("hello") == 5  # check pop_value
_.set_database({"hi": 6, "bye": 5})  # check set_database
assert _.get_database() == {"hi": 6, "bye": 5}  # check get_database
del _
