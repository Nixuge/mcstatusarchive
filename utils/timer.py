import time


class Timer:
    start_time: int
    last_step_time: int
    def __init__(self) -> None:
        self.start_time = time.time_ns()
        self.last_step_time = 0
    
    # calculate timing
    def _ct(self, minus: int) -> str:
        return "{:.2f}".format((time.time_ns() - minus) / 1000000000)

    def step(self) -> str:
        if self.last_step_time != 0:
            to_return = f"Took {self._ct(self.last_step_time)}s since last step, {self._ct(self.start_time)}s since the beginning"
            self.last_step_time = time.time_ns()
            return to_return
        return f"Took {self._ct(self.start_time)}s"
        

    def end(self) -> str:
        if self.last_step_time != 0:
            return f"Took {self._ct(self.last_step_time)}s since last step, {self._ct(self.start_time)}s total"
        return f"Took {self._ct(self.start_time)}s"