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
    start_times: dict[str, int]
    def __init__(self) -> None:
        self.start_times = {}
        self.total_time = 0
    
    def start_time(self, key: str) -> None:
        self.start_times[key] = time.time_ns()
    
    def end_time(self, key: str) -> None:
        self.total_time += (time.time_ns() - self.start_times[key])

    def stop(self) -> tuple[str, str]:
        time_total = self.total_time / 1000000000
        time_average = time_total / len(self.start_times)
        return "{:.2f}".format(time_total), "{:.2f}".format(time_average)

class CumulativeTimers:
    cumulative_timers: dict[str, CumulativeTimer] = {}
    # @classmethod
    # def add_timers(cls, *timers: str):
    #     for timer in timers:
    #         cls.add_timer(timer)
    # @classmethod
    # def add_timer(cls, timer_name: str):
    #     cls.cumulative_timers[timer_name] = CumulativeTimer()

    @classmethod
    def remove_timers(cls, *timers: str):
        for timer in timers:
            cls.remove_timer(timer)
    @classmethod
    def remove_timer(cls, timer_name: str):
        if timer_name in cls.cumulative_timers.keys():
            cls.cumulative_timers.pop(timer_name)
    
    @classmethod
    def get_timer(cls, timer_name: str) -> CumulativeTimer:
        timer = cls.cumulative_timers.get(timer_name)
        if timer == None:
            timer = CumulativeTimer()
            cls.cumulative_timers[timer_name] = timer
        return timer


    
