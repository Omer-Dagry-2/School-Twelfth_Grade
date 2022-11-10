from typing import *


class Database:
    def __init__(self):
        self.__database = {}

    def set_database(self, dic: dict) -> bool:
        """ set self.__database """
        self.__database = dic
        return True

    def get_database(self) -> dict:
        """ get self.__database """
        return self.__database

    def __setitem__(self, key: Hashable, val: Any) -> bool:
        """ add key: val """
        try:
            if not isinstance(key, Hashable):
                key_type = str(type(key)).split("'")[1]
                raise TypeError(f"{key} (type: {key_type}) can't be a key in "
                                f"the __database, only hashable types can be keys.")
            self.__database[key] = val
            return True
        except:
            return False

    def set_value(self, key: Hashable, val: Any) -> bool:
        """ add key: val """
        return self.__setitem__(key, val)

    def __getitem__(self, key: Hashable) -> Any:
        """ get the val of key """
        if key in self.__database.keys():
            val = self.__database[key]
            return val
        else:
            raise KeyError(f"{key} isn't a key in the __database.")

    def get_value(self, key: Hashable) -> Any:
        """ get the val of key """
        return self.__getitem__(key)

    def pop(self, key: Hashable) -> Any:
        """ remove key and self.__database[key] value """
        if key in self.__database.keys():
            return self.__database.pop(key)
        else:
            raise KeyError(f"{key} isn't a key in the __database.")

    def delete_value(self, key: Hashable) -> Any:
        """ remove key and self.__database[key] value """
        return self.pop(key)


_ = Database()
_["hello"] = 5  # check set_value
assert _["hello"] == 5  # check get_value
assert _.pop("hello") == 5  # check pop_value
_.set_database({"hi": 6, "bye": 5})  # check set_database
assert _.get_database() == {"hi": 6, "bye": 5}  # check get_database
del _