# Discord MPRIS

A small Linux service that reads the currently playing track from MPRIS and shows it as Discord Rich Presence.

It works with MPRIS-compatible players on GNOME, KDE, and other Linux desktops, including GNOME Music.

## Features

- Shows the current track and artist in Discord.
- Updates when playback or track metadata changes.
- Shows whether playback is active or paused.
- Prefers a playing player when more than one MPRIS player is available.

Album-cover lookup is not implemented. The activity uses image assets configured for the Discord application.

## Requirements

- Linux with a desktop D-Bus session
- Python 3 and `pip`
- A music player that exposes MPRIS metadata
- The Discord desktop application

The Python dependencies are installed from `requirements.txt`. No Cairo, PyGObject, or Playerctl development packages are required.

## Setup

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/MarM25/discord-mpris.git
cd discord-mpris
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Discord application

The service uses a Discord Application ID and the image asset keys `music`, `play`, and `pause`.

1. Create an application in the [Discord Developer Portal](https://discord.com/developers/applications).
2. Copy its Application ID into the `Presence(...)` call in `main.py`.
3. Add image assets named `music`, `play`, and `pause` under **Rich Presence > Art Assets** in the application settings.
4. In Discord, enable **User Settings > Activity Privacy > Share your detected activities with others**.

## Run

Keep Discord open, activate the virtual environment, then start the service:

```bash
source .venv/bin/activate
python main.py
```

Press `Ctrl+C` to stop it. The service clears the Discord activity when no playing or paused MPRIS player is available.

## Troubleshooting

- **No activity appears:** Use the Discord desktop app, check the activity-privacy setting, and verify that your player is exposing MPRIS metadata.
- **Missing image:** Confirm the three image asset keys are uploaded to the Discord application used by the service.
- **No connection to Discord at startup:** Leave Discord open; the service retries the connection every 10 seconds.
