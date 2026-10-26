import asyncio

from dbus_fast import BusType, MessageType
from dbus_fast.aio import MessageBus

from . import cover_art, discord_presence, mpris

REFRESH_LOCK = asyncio.Lock()


async def add_match(bus, rule):
    await mpris.call_bus(
        bus,
        mpris.DBUS_SERVICE,
        mpris.DBUS_PATH,
        mpris.DBUS_INTERFACE,
        "AddMatch",
        "s",
        [rule],
    )


async def refresh_presence(bus):
    async with REFRESH_LOCK:
        player = await mpris.get_player_presence(bus)
        if player is None:
            await discord_presence.clear_presence()
            return

        cover_url = player["art_url"]
        if not isinstance(cover_url, str) or not cover_url.startswith("https://"):
            cover_url = await cover_art.find_cover_art(
                player["artists"], player["album"]
            )

        await discord_presence.update_presence(player, cover_url)


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

        if message.interface == mpris.DBUS_INTERFACE and message.member == "NameOwnerChanged":
            if message.body[0].startswith(mpris.MPRIS_PREFIX):
                asyncio.create_task(refresh_presence(bus))
        elif (
            message.interface == mpris.PROPERTIES_INTERFACE
            and message.member == "PropertiesChanged"
            and message.body[0] == mpris.PLAYER_INTERFACE
        ):
            asyncio.create_task(refresh_presence(bus))
        return False

    bus.add_message_handler(on_message)
    await discord_presence.connect_rpc()
    await refresh_presence(bus)
    print("Watching MPRIS players...")
    await asyncio.Event().wait()


def run():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped")