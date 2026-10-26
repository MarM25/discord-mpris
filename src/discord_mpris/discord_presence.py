import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from pypresence import Presence

RPC = Presence("440997014315204609")
RPC_EXECUTOR = ThreadPoolExecutor(max_workers=1)


async def rpc_call(method, *args, **kwargs):
    loop = asyncio.get_running_loop()
    call = partial(method, *args, **kwargs)
    return await loop.run_in_executor(RPC_EXECUTOR, call)


async def connect_rpc():
    while True:
        try:
            await rpc_call(RPC.connect)
            print("Discord RPC connected")
            return
        except Exception as error:
            print(f"Discord is unavailable ({error}); retrying in 10 seconds...")
            await asyncio.sleep(10)


async def send_rpc(method, *args, **kwargs):
    try:
        await rpc_call(method, *args, **kwargs)
    except Exception as error:
        print(f"Discord RPC connection lost ({error}); reconnecting...")
        await connect_rpc()
        await rpc_call(method, *args, **kwargs)


async def update_presence(player, cover_url):
    song = player["song"]
    status = player["status"]
    activity_name = song or "Music"
    if len(activity_name) > 128:
        activity_name = activity_name[:125].rstrip() + "..."

    await send_rpc(
        RPC.update,
        name=activity_name,
        state=status,
        details=song or "Music",
        large_image=cover_url,
        large_text=song or "Music",
        small_image="play" if status == "Playing" else "pause",
    )


async def clear_presence():
    await send_rpc(RPC.clear)