import time
from concurrent.futures import ThreadPoolExecutor
from queue import Empty, Queue

from loguru import logger


def producer(queue: Queue) -> None:
    for i in range(2):
        time.sleep(1)
        item = f"Item {i}"
        queue.put(item)
        logger.info(f"Produced: {item}")
    logger.info("Exiting producer")


def consumer(queue: Queue) -> None:
    try:
        while True:
            time.sleep(2)
            # Wait at most 3 seconds for new item to appear
            item = queue.get(timeout=3)
            logger.info(f"Consumed: {item}")
            if item is None:
                break
    except Empty:
        logger.info("No more items in queue, exiting consumer")


if __name__ == "__main__":
    with (
        ThreadPoolExecutor(max_workers=4) as producer_executor,
        ThreadPoolExecutor(max_workers=3) as consumer_executor,
    ):
        queue = Queue()
        futures = []

        # Add tasks
        for i in range(4):
            # Tasks itself may add more tasks if executor is passed as argument
            future1 = producer_executor.submit(producer, queue)
            future2 = consumer_executor.submit(consumer, queue)
            futures += [future1, future2]

        # Optionally wait for tasks to finish
        # for i in as_completed(futures):
        #     logger.info(i)

        # Will only exit the 'with' statement when all executors are done
