import asyncio


def run_sync(coroutine):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        asyncio.ensure_future(coroutine, loop=loop)
    else:
        asyncio.run(coroutine)
