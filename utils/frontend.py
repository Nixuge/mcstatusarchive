import asyncio
import base64
import logging
from threading import Thread
from time import sleep
import httpx

UPDATE_URL = "http://127.0.0.1:50474/update_fields"

# TODO: support errors & bedrock

class FrontendUpdater(Thread):
    updates: list[dict]
    loop: asyncio.AbstractEventLoop

    def __init__(self) -> None:
        super().__init__(None, None, "FrontendUpdaterThread") 
        self.updates = []
        self.loop = asyncio.get_event_loop()
    
    def add_update(self, table_name: str, update: dict):
        update = dict(update) # new dict

        favicon = update.get("favicon")
        if favicon and not favicon == "None":
            update["favicon"] = base64.b64encode(update["favicon"]).decode('ascii')
        
        self.updates.append({
            "table_name": table_name,
            "fields": update
        })

    def _send_update(self, update: dict | list[dict]):
        httpx.post(UPDATE_URL, json=update)

    def _process_updates(self) -> None:
        try:
            all_updates = []

            while len(self.updates) > 0:
                all_updates.append(self.updates.pop(0))
            
            self._send_update(all_updates)
                        
        except:
            logging.error("Error on frontend update thread !")
            logging.error("TODO: HANDLE THIS ON Errors.PY")


    def run(self) -> None:
        while True:
            sleep(30)

            # perform create table queries BEFORE insert queries
            if len(self.updates) > 0:
                self._process_updates()