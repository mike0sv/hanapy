import asyncio
import logging
from logging.handlers import QueueHandler, QueueListener
from queue import Queue

from rich.console import Console
from rich.logging import RichHandler


async def _init_logger(level=logging.CRITICAL):
    log = logging.getLogger()
    log.setLevel(level)
    que: Queue = Queue()
    log.addHandler(QueueHandler(que))

    handler = RichHandler(console=Console(stderr=True), show_time=False)
    listener = QueueListener(que, handler)
    try:
        listener.start()
        while True:
            await asyncio.sleep(60)
    finally:
        listener.stop()


async def init_logger(level=logging.CRITICAL):
    _ = asyncio.create_task(_init_logger(level))
    await asyncio.sleep(0)
