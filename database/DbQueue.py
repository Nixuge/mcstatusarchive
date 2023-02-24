from sqlite3 import Connection, Cursor
from threading import Thread
from time import sleep


class DbQueue(Thread):
    # should be thread safe as lists are thread safe
    #TODO: use queue (https://www.geeksforgeeks.org/queue-in-python/ ?)
    instructions: list[tuple[str, str]] #0 = query, 1 = data
    connection: Connection
    cursor: Cursor

    def __init__(self, connection: Connection) -> None:
        super().__init__(None, None, "DbQueueThread") #see thread init (unneeded basically)
        self.instructions = []
        self.connection = connection
        self.cursor = connection.cursor()

    def add_instuction(self, query: str, data: str):
        self.instructions.append((query, data))

    def run(self) -> None:
        while True:
            sleep(0.5)
            if len(self.instructions) > 0:
                # count = 0
                for instruction in self.instructions:
                    # count += 1
                    self.cursor.execute(instruction[0], instruction[1])
                    self.instructions.remove(instruction) 
                # print(f"Added {count} values")

                self.connection.commit()
                self.connection.serialize()

