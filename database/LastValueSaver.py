import csv
import logging
import os
import sys
from threading import Thread
from time import sleep
from typing import Any
import bson

from vars.Errors import ErrorHandler
class LastValueSaver(Thread):
    filename: str
    content: dict
    changed: bool
    def __init__(self, filename: str) -> None:
        super().__init__(None, None, f"LastValueSaver-{filename}")
        self.filename = filename
        if not os.path.isfile(filename):
            with open(filename, "wb") as file:
                file.write(bson.dumps({}))
        try:
            with open(filename, "rb") as file:
                self.content = bson.loads(file.read()) # type: ignore
        except:
            ErrorHandler.add_error("last_value_bson_load")
        
        self.changed = True
        logging.info(f"Started LastValueSaver for file \"{filename}\"")

    def get_values(self, table_name: str) -> dict[str, Any] | None:
        data = self.content.get(table_name)
        if data == None:
            return None
        return dict(data) # CLONE DICT to avoid it being changed outside & wrongfully changed here as a result.

    def set_value(self, table_name: str, column: str, data: Any):
        # Note: bigger ints turn into int64s, but shouldn't be an issue here
        server_dict = self.content.get(table_name)
        if not server_dict:
            self.content[table_name] = {}
        self.content[table_name][column] = data
        # Since the row duplicates are checked at another place, this shouldn't need any other checks for that here.
        self.changed = True 

    def save_to_file(self):
        if not self.changed:
            return
        try:
            with open(self.filename, "wb") as file:
                data = bson.dumps(dict(self.content))
                file.write(data)
                # print("Saved successfully" + str(self.content))
        except:
            ErrorHandler.add_error("last_value_bson_save", {"file": self.filename})
        self.changed = False
    
    def run(self) -> None:
        while not ErrorHandler.should_stop:
            sleep(5)
            self.save_to_file()
        
        logging.info(f"Stopped '{self.filename}' LastValueSaver thread gracefully.")
