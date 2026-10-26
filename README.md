# Discord MPRIS

A small Linux service that reads the currently playing track from MPRIS and shows it as Discord Rich Presence.

It works with MPRIS-compatible players on GNOME, KDE, and other Linux desktops.

## Project Origin

This project started from [RayzrDev/discord-rpc-mpris](https://github.com/rayzrdev/discord-rpc-mpris). The current implementation has since been rewritten from scratch, but i want to appreciate their work.

## Features

- Shows the current track and artist in Discord.
- Uses the player's cover URL when available, then tries MusicBrainz and the Cover Art Archive.
- Updates when playback or track metadata changes.
- Shows whether playback is active or paused.
- Prefers a playing player when more than one MPRIS player is available.

If no cover is available from the player or the Cover Art Archive, no large image is set. Results, including misses, are cached until the service exits.

## Requirements

- Linux with a desktop D-Bus session
- Python 3 and `pip`
- A music player that exposes MPRIS metadata
- The Discord desktop application

The Python dependencies are declared in `pyproject.toml`.

## Setup

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/MarM25/discord-mpris.git
cd discord-mpris
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

### Discord application

The service uses a Discord Application ID and the image asset keys `play` and `pause` for playback status. Cover art is looked up per album.

1. Create an application in the [Discord Developer Portal](https://discord.com/developers/applications).
2. Copy its Application ID into the `Presence(...)` call in `src/discord_mpris/discord_presence.py`.
3. Add image assets named `play` and `pause` under **Rich Presence > Art Assets** in the application settings.
4. In Discord, enable **User Settings > Activity Privacy > Share your detected activities with others**.

## Run

Keep Discord open, activate the virtual environment, then start the service:

```bash
source .venv/bin/activate
python3 -m discord_mpris
```

Press `Ctrl+C` to stop it. The service clears the Discord activity when no playing or paused MPRIS player is available.

## Troubleshooting

- **No activity appears:** Use the Discord desktop app, check the activity-privacy setting, and verify that your player is exposing MPRIS metadata.
- **Missing playback icon:** Confirm the `play` and `pause` image assets are uploaded to the Discord application used by the service.
- **No connection to Discord at startup:** Leave Discord open; the service retries the connection every 10 seconds.

## Development

Run the test suite with the standard library:

```bash
python -m unittest discover -s tests
```

## AI Disclosure

This repository is primarily written with the assistance of AI tools.
