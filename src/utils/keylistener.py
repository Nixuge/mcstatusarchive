import logging
import tty
import termios
import asyncio
import sys

from utils.errors import ErrorHandler

class KeyListenerData:
    reload_requested = False


def setup_stdin_keylistener(loop: asyncio.AbstractEventLoop):
    if not sys.stdin.isatty():
        return lambda: None

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    def on_key():
        try:
            ch = sys.stdin.read(1)
            # \x12 is Ctrl+R, 'r' or 'R'
            if ch in ('\x12'):
                KeyListenerData.reload_requested = True
                logging.info("Reload requested (Ctrl+R / r detected). Will reload servers on next run.")
            elif ch == '\x03':  # Ctrl+C
                ErrorHandler.should_stop = True
        except Exception:
            pass

    try:
        tty.setcbreak(fd)
        loop.add_reader(fd, on_key)
    except Exception as e:
        logging.warning(f"Could not setup keylistener: {e}")

    def cleanup():
        try:
            loop.remove_reader(fd)
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except Exception:
            pass

    return cleanup
