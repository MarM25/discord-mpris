"""Show the current MPRIS track as Discord Rich Presence."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from dbus_fast import BusType, Message, MessageType, Variant
from dbus_fast.aio import MessageBus
from pypresence import Presence

DBUS_SERVICE = "org.freedesktop.DBus"
DBUS_PATH = "/org/freedesktop/DBus"
DBUS_INTERFACE = "org.freedesktop.DBus"
MPRIS_PREFIX = "org.mpris.MediaPlayer2."
MPRIS_PATH = "/org/mpris/MediaPlayer2"
PLAYER_INTERFACE = "org.mpris.MediaPlayer2.Player"
PROPERTIES_INTERFACE = "org.freedesktop.DBus.Properties"

RPC = Presence("440997014315204609")
RPC_EXECUTOR = ThreadPoolExecutor(max_workers=1)
REFRESH_LOCK = asyncio.Lock()


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


async def call_bus(bus, destination, path, interface, member, signature="", body=None):
    reply = await bus.call(
        Message(
            destination=destination,
            path=path,
            interface=interface,
            member=member,
            signature=signature,
            body=body or [],
        )
    )
    if reply.message_type == MessageType.ERROR:
        raise RuntimeError(reply.body[0] if reply.body else reply.error_name)
    return reply.body


def unwrap(value):
    if isinstance(value, Variant):
        return unwrap(value.value)
    if isinstance(value, dict):
        return {key: unwrap(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [unwrap(item) for item in value]
    return value


async def get_player_presence(bus):
    names = await call_bus(
        bus, DBUS_SERVICE, DBUS_PATH, DBUS_INTERFACE, "ListNames"
    )
    players = []

    for name in sorted(names[0]):
        if not name.startswith(MPRIS_PREFIX):
            continue
        try:
            result = await call_bus(
                bus,
                name,
                MPRIS_PATH,
                PROPERTIES_INTERFACE,
                "GetAll",
                "s",
                [PLAYER_INTERFACE],
            )
        except Exception:
            continue

        properties = unwrap(result[0])
        status = properties.get("PlaybackStatus")
        if status not in ("Playing", "Paused"):
            continue

        metadata = properties.get("Metadata", {})
        title = metadata.get("xesam:title")
        artists = metadata.get("xesam:artist", [])
        if isinstance(artists, str):
            artists = [artists]
        artist = ", ".join(artists)
        song = " - ".join(part for part in (title, artist) if part)
        players.append((status, song, name))

    return next((player for player in players if player[0] == "Playing"), None) or next(
        iter(players), None
    )


async def send_rpc(method, *args, **kwargs):
    try:
        await rpc_call(method, *args, **kwargs)
    except Exception as error:
        print(f"Discord RPC connection lost ({error}); reconnecting...")
        await connect_rpc()
        await rpc_call(method, *args, **kwargs)


async def refresh_presence(bus):
    async with REFRESH_LOCK:
        player = await get_player_presence(bus)
        if player is None:
            await send_rpc(RPC.clear)
            return

        status, song, _name = player
        if status == "Playing":
            await send_rpc(
                RPC.update,
                state="Playing",
                details=song or "Listening to music",
                large_image="music",
                large_text=song or "Music",
                small_image="play",
            )
        else:
            await send_rpc(
                RPC.update,
                state="Paused",
                details=song or "Music",
                large_image="music",
                large_text=song or "Music",
                small_image="pause",
            )


async def add_match(bus, rule):
    await call_bus(
        bus,
        DBUS_SERVICE,
        DBUS_PATH,
        DBUS_INTERFACE,
        "AddMatch",
        "s",
        [rule],
    )


async def main():
    bus = await MessageBus(bus_type=BusType.SESSION).connect()
    await add_match(
        bus,
        "type='signal',sender='org.freedesktop.DBus',"
        "interface='org.freedesktop.DBus',member='NameOwnerChanged'",
    )
    await add_match(
        bus,
        "type='signal',interface='org.freedesktop.DBus.Properties',"
        "member='PropertiesChanged',path='/org/mpris/MediaPlayer2'",
    )

    def on_message(message):
        if message.message_type != MessageType.SIGNAL:
            return False

        if message.interface == DBUS_INTERFACE and message.member == "NameOwnerChanged":
            if message.body[0].startswith(MPRIS_PREFIX):
                asyncio.create_task(refresh_presence(bus))
        elif (
            message.interface == PROPERTIES_INTERFACE
            and message.member == "PropertiesChanged"
            and message.body[0] == PLAYER_INTERFACE
        ):
            asyncio.create_task(refresh_presence(bus))
        return False

    bus.add_message_handler(on_message)
    await connect_rpc()
    await refresh_presence(bus)
    print("Watching MPRIS players...")
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped")
