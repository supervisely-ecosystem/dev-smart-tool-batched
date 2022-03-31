import asyncio


def run_sync(coroutine):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        asyncio.create_task(coroutine)
    else:
        asyncio.run(coroutine)
