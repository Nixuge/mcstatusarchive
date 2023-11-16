import time


class Timer:
    start_time: int
    def __init__(self) -> None:
        self.start_time = time.time_ns()
    
    # calculate timing
    def _ct(self) -> str:
        return "{:.2f}".format((time.time_ns() - self.start_time) / 1000000000)

    def step(self) -> str:
        to_return = f"Took {self._ct()}s"
        self.start_time = time.time_ns()
        return to_return

    def end(self) -> str:
        return f"Took {self._ct()}s"