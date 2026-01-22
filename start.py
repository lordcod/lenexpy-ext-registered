import json
import logging
import traceback
import contextlib
import sys
import os

from loguru import logger


def init():
    logging.basicConfig(
        level=logging.DEBUG,
        filename="work.log",
    )
    log_level = "DEBUG"
    log_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS zz}</green> | <level>{level: <8}</level> | <yellow>Line {line: >4} ({file}):</yellow> <b>{message}</b>"
    logger.add(sys.stderr, level=log_level, format=log_format, colorize=True, backtrace=True, diagnose=True)
    logger.add("file.log", level=log_level, format=log_format, colorize=False, backtrace=True, diagnose=True)

    with contextlib.suppress(Exception):
        os.chdir(sys._MEIPASS)

    config = {}
    try:
        from app.menu import run_app

        with open("config.json", "rb") as file:
            config = json.loads(file.read())

        run_app(config)
    except BaseException:
        traceback.print_exc()
    finally:
        config.pop("lenex", None)
        with open("config.json", "wb+") as file:
            data = json.dumps(
                config,
                ensure_ascii=False,
                indent=4,
            ).encode()
            file.write(data)


if __name__ == "__main__":
    init()
