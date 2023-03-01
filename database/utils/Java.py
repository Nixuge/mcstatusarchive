from typing import Any


class JavaUtils:
    args_order = ("save_time", "players_on", "players_max", "ping", "players_sample", "version_protocol", "version_name", "motd", "favicon")
    @staticmethod
    def get_args_in_order_from_dict(args_dict: dict):
        # Convert a dict to a list of items in order
        ordered_args: list[Any] = []
        for key in JavaUtils.args_order:
            ordered_args.append(args_dict.get(key, None))
        return ordered_args