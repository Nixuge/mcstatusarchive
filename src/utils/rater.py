import random
from enum import Enum, auto


class ServerState(Enum):
    ACTIVE = auto()
    EMPTY = auto()
    DOWN = auto()


# ServerRater may not be the best classname tbh
class ServerRater:
    def __init__(
        self,
        skip_range_down: tuple[int, int] = (5, 10), # how many should skip when a server is down
        skip_range_empty: tuple[int, int] = (3, 5), # how many should skip when a server is empty
        down_threshold: int = 10, # how many consecutive down reports before setting the server as down
        history_size: int = 5, # how many player values kept in history at most
        empty_avg_threshold: float = 1.0, # threshold which if a server has its full history average below it will be set as empty
        burst_threshold: int = 5, # threshold above which if a server is reported, even if set as empty or smth before, it'll just get back to fully active
    ) -> None:
        self._skip_range_down = skip_range_down
        self._skip_range_empty = skip_range_empty
        self._down_threshold = down_threshold
        self._history_size = history_size
        self._empty_avg_threshold = empty_avg_threshold
        self._burst_threshold = burst_threshold

        self._state: ServerState = ServerState.ACTIVE
        self._cycles_until_poll: int = 0
        self._consecutive_down_count: int = 0
        self._playercount_history: list[int] = []


    def should_poll(self) -> bool:
        if self._cycles_until_poll > 0:
            self._cycles_until_poll -= 1
            return False
        return True

    def report_down(self) -> None:
        self._consecutive_down_count += 1

        if self._consecutive_down_count >= self._down_threshold:
            self._state = ServerState.DOWN
            # self._playercount_history.clear()
            self._cycles_until_poll = random.randint(*self._skip_range_down)
        else:
            self._cycles_until_poll = random.randint(0, 1)

    def report_success(self, players_online: int) -> None:
        self._consecutive_down_count = 0

        # burst of players 
        if players_online >= self._burst_threshold:
            self._playercount_history.clear()
            self._playercount_history.append(players_online)
            self._state = ServerState.ACTIVE
            self._cycles_until_poll = 0
            return


        # Normal append / cleanup
        self._playercount_history.append(players_online)
        while len(self._playercount_history) > self._history_size:
            self._playercount_history.pop(0)

        # not enough data
        if len(self._playercount_history) < self._history_size:
            if self._state is ServerState.DOWN:
                self._state = ServerState.ACTIVE
                self._cycles_until_poll = 0
            return

        # average (normal case)
        avg = sum(self._playercount_history) / len(self._playercount_history)
        if avg <= self._empty_avg_threshold:
            self._state = ServerState.EMPTY
            self._cycles_until_poll = random.randint(*self._skip_range_empty)
        else:
            self._state = ServerState.ACTIVE
            self._cycles_until_poll = 0

    @property
    def state(self) -> ServerState:
        return self._state
