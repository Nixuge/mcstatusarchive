from sqlite3 import Connection, Cursor
from threading import Thread
from time import sleep

from database.DbManager import DbInstance


class DbQueue(Thread):
    # should be thread safe as lists are thread safe
    #TODO: use queue (https://www.geeksforgeeks.org/queue-in-python/ ?)
    instructions: list[tuple[str, list | None]] #0 = query, 1 = data
    important_instructions: list[str]
    connection: Connection
    cursor: Cursor

    def __init__(self, db_manager: DbInstance) -> None:
        super().__init__(None, None, "DbQueueThread") #see thread init (unneeded basically)
        self.instructions = []
        self.important_instructions = []
        self.connection = db_manager.connection
        self.cursor = db_manager.cursor
    
    def add_important_instruction(self, full_query: str):
        self.important_instructions.append(full_query)

    def add_instuction(self, query: str, data: list | None):
        self.instructions.append((query, data))

    def run(self) -> None:
        while True:
            sleep(0.5)

            # perform create table queries BEFORE insert queries
            if len(self.important_instructions) > 0:
                for instruction in self.important_instructions:
                    self.cursor.execute(instruction)
                self.connection.commit()
                self.connection.serialize()
            
            if len(self.instructions) > 0:
                # count = 0
                for instruction in self.instructions:
                    # count += 1
                    if instruction[1] != None: # if data present
                        self.cursor.execute(instruction[0], instruction[1])
                    else:
                        self.cursor.execute(instruction[0])
                    
                    self.instructions.remove(instruction) 
                # print(f"Added {count} values")

                self.connection.commit()
                self.connection.serialize()

