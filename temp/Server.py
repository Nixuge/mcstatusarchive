class ServerSv:
    ip: str
    port: int

    values: dict

    def __init__(self, table_name: str, ip: str, port: int) -> None:
        self.ip = ip
        self.port = port
        self.values = {}
    
    def update_values(self, new_values: dict) -> dict:
        # not checking if new_values has all needed values in it
        changed_values = {}
        for key, val in new_values.items():
            if self.values.get(key) != val:
                self.values[key] = val    # save to class dict
                changed_values[key] = val # & to returned dict
        
        return changed_values
