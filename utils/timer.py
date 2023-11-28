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

class CumulativeTimer:
    total_time: float
    start_times: dict
    def __init__(self) -> None:
        self.start_times = {}
        self.total_time = 0
    
    def start_time(self, key: str) -> None:
        self.start_times[key] = time.time_ns()
    
    def end_time(self, key: str) -> None:
        self.total_time += (time.time_ns() - self.start_times.pop(key))

    def stop(self) -> str:
        return "{:.2f}".format(self.total_time / 1000000000)

class CumulativeTimers:
    cumulative_timers: dict
    @classmethod
    def add_timer(cls, timer_name: str):
        if not cls.cumulative_timers:
            cls.cumulative_timers = {}
        cls.cumulative_timers[timer_name] = CumulativeTimer()
    
    @classmethod
    def remove_timer(cls, timer_name: str):
        if cls.cumulative_timers and timer_name in cls.cumulative_timers.keys():
            cls.cumulative_timers.pop(timer_name)