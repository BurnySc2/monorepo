import asyncio

from loguru import logger


async def slow_function():
    await asyncio.sleep(3)
    text = 'We did it reddit'
    logger.info(text)
    return text


async def main():
    task = asyncio.create_task(slow_function())
    try:
        await asyncio.wait_for(task, timeout=1.1)
        assert False, 'Should never be reached'
    except asyncio.TimeoutError:
        assert task.cancelled() is True
        assert task.done() is True


if __name__ == '__main__':
    asyncio.run(main())
