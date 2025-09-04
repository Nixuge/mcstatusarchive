from abc import ABCMeta, abstractmethod
from typing import Any, Callable

# thanks to https://stackoverflow.com/a/45364670/10321409
class AsyncInit(object):
    """Inheriting this class allows you to define an async __init__.

    So you can create objects by doing something like `await MyClass(params)`
    """
    async def __new__(cls, *a, **kw):
        instance = super().__new__(cls)
        await instance.__init__(*a, **kw)
        return instance

    async def __init__(self):
        pass


class ServerSv(AsyncInit):
    ip: str
    port: int

    values: Any

    async def __init__(self, table_name: str, ip: str, port: int) -> None:
        self.ip = ip
        self.port = port

    @abstractmethod
    def update_values(self, new_values: Any) -> Any: pass
        # not checking if new_values has all needed values in it
        # changed_values = {}
        # for key, val in new_values.items():
        #     if self.values.get(key) != val:
        #         self.values[key] = val    # save to class dict
        #         changed_values[key] = val  # & to returned dict

        # return changed_values

    @abstractmethod
    async def save_status(self): pass


class DbUpdater:
    base_table_name: str
    func_per_field: dict[Any, Callable]

    @abstractmethod
    def __init__(self, base_table_name: str) -> None:
        raise Exception("Called init on abstract DbUpdater.")
    
    @abstractmethod
    def create_dbs(self) -> None:
        raise Exception("Called create_dbs_if_not_exist on abstract DbUpdater.")

    @abstractmethod
    def load_previous_values(self) -> Any:
        raise Exception("Called load_previous_values on abstract DbUpdater.")
    
    @abstractmethod
    def update_all_changed(self, values: Any, changed_fields: list[Any]):
        raise Exception("Called update_all_changed on abstract DbUpdater.")