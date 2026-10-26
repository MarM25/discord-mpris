from dbus_fast import Message, MessageType, Variant

DBUS_SERVICE = "org.freedesktop.DBus"
DBUS_PATH = "/org/freedesktop/DBus"
DBUS_INTERFACE = "org.freedesktop.DBus"
MPRIS_PREFIX = "org.mpris.MediaPlayer2."
MPRIS_PATH = "/org/mpris/MediaPlayer2"
PLAYER_INTERFACE = "org.mpris.MediaPlayer2.Player"
PROPERTIES_INTERFACE = "org.freedesktop.DBus.Properties"


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
        players.append(
            {
                "status": status,
                "song": song,
                "name": name,
                "artists": artists,
                "album": metadata.get("xesam:album"),
                "art_url": metadata.get("mpris:artUrl"),
            }
        )

    return next(
        (player for player in players if player["status"] == "Playing"), None
    ) or next(iter(players), None)