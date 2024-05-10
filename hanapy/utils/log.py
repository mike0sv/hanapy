import asyncio
import logging
from logging.handlers import QueueHandler, QueueListener
from queue import Queue


async def _init_logger(level=logging.CRITICAL):
    # logging.basicConfig(level=level)
    log = logging.getLogger()
    log.setLevel(level)
    que: Queue = Queue()
    log.addHandler(QueueHandler(que))
    log.setLevel(logging.DEBUG)
    listener = QueueListener(que, logging.StreamHandler())
    try:
        listener.start()
        while True:
            await asyncio.sleep(60)
    finally:
        listener.stop()


async def init_logger(level=logging.CRITICAL):
    _ = asyncio.create_task(_init_logger(level))
    await asyncio.sleep(0)
