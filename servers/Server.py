from abc import abstractmethod

# class aobject(object):
#     """Inheriting this class allows you to define an async __init__.

#     So you can create objects by doing something like `await MyClass(params)`
#     """
#     async def __new__(cls, *a, **kw):
#         instance = super().__new__(cls)
#         await instance.__init__(*a, **kw)
#         return instance

#     async def __init__(self):
#         pass


class ServerSv:
    ip: str
    port: int

    values: dict

    def __init__(self, table_name: str, ip: str, port: int) -> None:
        self.ip = ip
        self.port = port

    def update_values(self, new_values: dict) -> dict:
        # not checking if new_values has all needed values in it
        changed_values = {}
        for key, val in new_values.items():
            if self.values.get(key) != val:
                self.values[key] = val    # save to class dict
                changed_values[key] = val  # & to returned dict

        return changed_values

    @abstractmethod
    async def save_status(self): pass
