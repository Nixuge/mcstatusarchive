import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from asyncio import Task
from time import time
import logging

try:
    from utils.logger import get_proper_logger
    logger = get_proper_logger(logging.getLogger("root"), False)
except ImportError:
    logging.basicConfig(level=logging.INFO)

import re
import shutil

from db.database import Database
from db.schema import SERVER_TYPE_JAVA, SERVER_TYPE_BEDROCK
from db.deduplicators import DedupGetType
from config import Paths, Timings
from utils.errors import ErrorHandler, ErrorKey
from servers.base import PollResult, PollStatus
from servers.loader import ServersLoader
from utils.keylistener import KeyListenerData, setup_stdin_keylistener


# Note: mainly claude'd bc i can't b bothered writing weird ansi escape sequences
ANSI_ESCAPE_RE = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')


def visible_len(s: str) -> int:
    return len(ANSI_ESCAPE_RE.sub('', s))


def wrap_prop_lines(prefix: str, prop_counts: dict[str, int], width: int) -> list[str]:
    if not prop_counts:
        return [f"{prefix}none"]

    sorted_items = sorted(prop_counts.items(), key=lambda x: x[1], reverse=True)
    tokens = [f"{k}: \033[94m{v:,}\033[0m" for k, v in sorted_items]

    lines = []
    current_line = prefix
    current_vis_len = visible_len(prefix)
    indent = "    "
    indent_vis_len = len(indent)

    for token in tokens:
        sep = ", " if current_line not in (prefix, indent) else ""
        token_vis_len = visible_len(token) + len(sep)

        if current_vis_len + token_vis_len > width and current_line.strip():
            lines.append(current_line)
            current_line = indent + token
            current_vis_len = indent_vis_len + visible_len(token)
        else:
            current_line += sep + token
            current_vis_len += token_vis_len

    if current_line.strip():
        lines.append(current_line)

    return lines


def print_status_block(j_counts: dict, j_total: int,
                       b_counts: dict, b_total: int,
                       j_prop_counts: dict[str, int] | None = None,
                       b_prop_counts: dict[str, int] | None = None,
                       dedup_counts: dict | None = None,
                       start_time: float | None = None,
                       last_line_count: list[int] | None = None,
                       is_first: bool = False):
    width = max(shutil.get_terminal_size((80, 20)).columns - 1, 40)
    
    if start_time is not None:
        elapsed = time() - start_time
        if elapsed < 60:
            time_str = f" {elapsed:.1f}s "
        else:
            mins = int(elapsed // 60)
            secs = elapsed % 60
            time_str = f" {mins}m {secs:04.1f}s "

        target_len = min(36, width)
        remaining = max(4, target_len - len(time_str) - 2)
        left = remaining // 2
        right = remaining - left
        top_divider = f"{'=' * left}[\033[96m{time_str}\033[0m]{'=' * right}"
        bottom_divider = "=" * (left + len(time_str) + 2 + right)
    else:
        top_divider = "IS NONE?"
        # top_divider = "=" * min(30, width)
        bottom_divider = top_divider

    j_str = (
        f"Java: {j_counts['done']}/{j_total} "
        f"[\033[96m{j_counts['processing']} processing\033[0m] "
        f"(\033[92m{j_counts['success']}\033[0m/"
        f"\033[91m{j_counts['fail']}\033[0m/"
        f"\033[93m{j_counts['skip']}\033[0m/"
        f"\033[38;5;208m{j_counts['save_fail']}\033[0m/"
        f"\033[95m{j_counts['other']}\033[0m)"
    )
    b_str = (
        f"Bedrock: {b_counts['done']}/{b_total} "
        f"[\033[96m{b_counts['processing']} processing\033[0m] "
        f"(\033[92m{b_counts['success']}\033[0m/"
        f"\033[91m{b_counts['fail']}\033[0m/"
        f"\033[93m{b_counts['skip']}\033[0m/"
        f"\033[38;5;208m{b_counts['save_fail']}\033[0m/"
        f"\033[95m{b_counts['other']}\033[0m)"
    )
    lines = [
        top_divider,
        j_str,
        *wrap_prop_lines("  Props: ", j_prop_counts or {}, width),
        b_str,
        *wrap_prop_lines("  Props: ", b_prop_counts or {}, width),
    ]
    if dedup_counts is not None:
        jt_c = dedup_counts["java_text_cache"]
        jt_d = dedup_counts["java_text_db"]
        jt_a = dedup_counts["java_text_add"]
        bt_c = dedup_counts["bedrock_text_cache"]
        bt_d = dedup_counts["bedrock_text_db"]
        bt_a = dedup_counts["bedrock_text_add"]
        p_c = dedup_counts["player_cache"]
        p_d = dedup_counts["player_db"]
        p_a = dedup_counts["player_add"]
        lines.append(f"Dedup Text (Java):    \033[92m{jt_c:,} cache\033[0m | \033[93m{jt_d:,} db\033[0m | \033[96m{jt_a:,} new\033[0m")
        lines.append(f"Dedup Text (Bedrock): \033[92m{bt_c:,} cache\033[0m | \033[93m{bt_d:,} db\033[0m | \033[96m{bt_a:,} new\033[0m")
        lines.append(f"Dedup Players:        \033[92m{p_c:,} cache\033[0m | \033[93m{p_d:,} db\033[0m | \033[96m{p_a:,} new\033[0m")

    lines.append(bottom_divider)
    cur_count = len(lines)
    prev_count = last_line_count[0] if (last_line_count is not None and not is_first) else 0

    if is_first or prev_count == 0:
        print("\n".join(lines), flush=True)
    else:
        # Move up prev_count lines and clear each line as it prints
        out = [f"\033[{prev_count}A\r"]
        for line in lines:
            out.append(f"\033[K{line}\n")
        # Clear any leftover lines if new block is shorter than previous
        for _ in range(prev_count - cur_count):
            out.append("\033[K\n")
        print("".join(out), end="", flush=True)

    if last_line_count is not None:
        last_line_count[0] = cur_count


async def run_batch_limit(servers: list, primary_limit: int = 100, max_limit: int = 500, stall_timeout: float = 1.0):
    total = len(servers)
    if total == 0:
        return

    start_time = time()
    java_total = sum(1 for s in servers if s.db.server_type == SERVER_TYPE_JAVA)
    bedrock_total = total - java_total

    dedup_counts = {
        "java_text_cache": 0, "java_text_db": 0, "java_text_add": 0,
        "bedrock_text_cache": 0, "bedrock_text_db": 0, "bedrock_text_add": 0,
        "player_cache": 0, "player_db": 0, "player_add": 0,
    }
    j_counts = {"done": 0, "processing": 0, "success": 0, "fail": 0, "skip": 0, "save_fail": 0, "other": 0}
    b_counts = {"done": 0, "processing": 0, "success": 0, "fail": 0, "skip": 0, "save_fail": 0, "other": 0}
    j_prop_counts: dict[str, int] = {}
    b_prop_counts: dict[str, int] = {}
    last_line_count = [0]

    # Initial render
    print_status_block(j_counts, java_total, b_counts, bedrock_total, j_prop_counts, b_prop_counts, dedup_counts, start_time=start_time, last_line_count=last_line_count, is_first=True)

    primary_sem = asyncio.Semaphore(primary_limit)
    max_sem = asyncio.Semaphore(max_limit)
    loop = asyncio.get_running_loop()

    async def poll_worker(server):
        is_java = (server.db.server_type == SERVER_TYPE_JAVA)
        target_counts = j_counts if is_java else b_counts
        target_prop_counts = j_prop_counts if is_java else b_prop_counts

        async with max_sem:
            await primary_sem.acquire()
            primary_released = False

            def release_primary():
                nonlocal primary_released
                if not primary_released:
                    primary_released = True
                    primary_sem.release()

            timer_handle = loop.call_later(stall_timeout, release_primary)
            target_counts["processing"] += 1
            print_status_block(j_counts, java_total, b_counts, bedrock_total, j_prop_counts, b_prop_counts, dedup_counts, start_time=start_time, last_line_count=last_line_count, is_first=False)
            try:
                res = await server.poll_and_save()
            finally:
                target_counts["processing"] -= 1
                timer_handle.cancel()
                release_primary()

            target_counts["done"] += 1
            for prop in res.updated_properties:
                target_prop_counts[prop] = target_prop_counts.get(prop, 0) + 1

            if res.status == PollStatus.SUCCESS:
                target_counts["success"] += 1
            elif res.status == PollStatus.FAIL:
                target_counts["fail"] += 1
            elif res.status == PollStatus.SKIP:
                target_counts["skip"] += 1
            elif res.status == PollStatus.SAVE_FAIL:
                target_counts["save_fail"] += 1
            else:
                target_counts["other"] += 1

            text_cache_key = "java_text_cache" if is_java else "bedrock_text_cache"
            text_db_key = "java_text_db" if is_java else "bedrock_text_db"
            text_add_key = "java_text_add" if is_java else "bedrock_text_add"

            for t in res.text_dedups:
                if t == DedupGetType.CACHE:
                    dedup_counts[text_cache_key] += 1
                elif t == DedupGetType.DB:
                    dedup_counts[text_db_key] += 1
                elif t == DedupGetType.ADD:
                    dedup_counts[text_add_key] += 1

            for p in res.player_dedups:
                if p == DedupGetType.CACHE:
                    dedup_counts["player_cache"] += 1
                elif p == DedupGetType.DB:
                    dedup_counts["player_db"] += 1
                elif p == DedupGetType.ADD:
                    dedup_counts["player_add"] += 1

            print_status_block(j_counts, java_total, b_counts, bedrock_total, j_prop_counts, b_prop_counts, dedup_counts, start_time=start_time, last_line_count=last_line_count, is_first=False)

    await asyncio.gather(*(poll_worker(s) for s in servers))




async def save_every_x_secs(servers: list, db_java: Database, db_bedrock: Database):
    current_servers = servers

    while True:
        if ErrorHandler.should_stop:
            logging.critical("Stop instruction found. Now stopping the app.")
            return

        if KeyListenerData.reload_requested:
            logging.info("Reloading servers from servers.json...")
            try:
                old_len = len(current_servers)
                current_servers = await ServersLoader(Paths.SERVERS_JSON, db_java, db_bedrock).parse()
                logging.info(f"Reload complete! {len(current_servers)} servers loaded.")
                ErrorHandler.add_warn(ErrorKey.WARN_LIVE_RELOAD, {"success": True, "old_len": old_len, "new_len": len(current_servers)})
            except Exception as e:
                logging.error(f"Failed to reload servers: {e}")
                ErrorHandler.add_warn(ErrorKey.WARN_LIVE_RELOAD, {"success": False, "error": str(e)})
            finally:
                KeyListenerData.reload_requested = False

        start_time = int(time())
        await run_batch_limit(current_servers)

        logging.info("[Waiting for timer to finish...]")
        while start_time + Timings.SAVE_EVERY > int(time()):
            if KeyListenerData.reload_requested or ErrorHandler.should_stop:
                break
            await asyncio.sleep(.01)


async def main():
    logging.info("Starting.")

    db_java = Database(Paths.DB_PATH_JAVA, SERVER_TYPE_JAVA)
    db_bedrock = Database(Paths.DB_PATH_BEDROCK, SERVER_TYPE_BEDROCK)

    servers = await ServersLoader(Paths.SERVERS_JSON, db_java, db_bedrock).parse()
    logging.info(f"{len(servers)} servers loaded.")

    loop = asyncio.get_running_loop()
    cleanup_keys = setup_stdin_keylistener(loop)

    try:
        await save_every_x_secs(servers, db_java, db_bedrock)
    except (asyncio.CancelledError, KeyboardInterrupt):
        ErrorHandler.should_stop = True
        logging.info("Excepting a graceful stop soon.")
    
    cleanup_keys()

if __name__ == "__main__":
    asyncio.run(main())
