import asyncio
import json
import re
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

MUSICBRAINZ_CACHE = {}
MUSICBRAINZ_LAST_REQUEST = 0.0
USER_AGENT = "discord-mpris/0.1 (https://github.com/MarM25/discord-mpris)"


def normalize_text(value):
    return " ".join(value.casefold().split())


def escape_musicbrainz_term(value):
    return re.sub(r'([+\-&|!(){}\[\]^"~*?:\\/])', r"\\\1", value)


def fetch_cover_art(artists, album):
    query = (
        f'release:"{escape_musicbrainz_term(album)}" AND '
        f'artist:"{escape_musicbrainz_term(artists[0])}"'
    )
    search_url = "https://musicbrainz.org/ws/2/release/?" + urlencode(
        {"query": query, "fmt": "json", "limit": 10}
    )
    request = Request(search_url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=8) as response:
            releases = json.load(response).get("releases", [])
    except (OSError, ValueError, TimeoutError) as error:
        raise OSError(f"MusicBrainz API request failed: {error}") from error

    wanted_artists = {normalize_text(artist) for artist in artists}
    for release in releases:
        if normalize_text(release.get("title", "")) != normalize_text(album):
            continue

        release_artists = {
            normalize_text(credit.get("name") or credit.get("artist", {}).get("name", ""))
            for credit in release.get("artist-credit", [])
            if isinstance(credit, dict)
        }
        if not wanted_artists.intersection(release_artists):
            continue

        release_id = release.get("id")
        if not release_id:
            continue

        cover_url = f"https://coverartarchive.org/release/{release_id}/front-500"
        cover_request = Request(
            cover_url, headers={"User-Agent": USER_AGENT}, method="HEAD"
        )
        try:
            with urlopen(cover_request, timeout=8):
                return cover_url
        except HTTPError as error:
            if error.code == 404:
                continue
            raise OSError(
                f"Cover Art Archive request for release {release_id} failed: {error}"
            ) from error
        except (OSError, TimeoutError) as error:
            raise OSError(
                f"Cover Art Archive request for release {release_id} failed: {error}"
            ) from error

    return None


async def find_cover_art(artists, album):
    global MUSICBRAINZ_LAST_REQUEST

    if not artists or not album:
        return None

    cache_key = (tuple(normalize_text(artist) for artist in artists), normalize_text(album))
    if cache_key in MUSICBRAINZ_CACHE:
        return MUSICBRAINZ_CACHE[cache_key]

    delay = 1.0 - (time.monotonic() - MUSICBRAINZ_LAST_REQUEST)
    if delay > 0:
        await asyncio.sleep(delay)
    MUSICBRAINZ_LAST_REQUEST = time.monotonic()

    try:
        cover_url = await asyncio.to_thread(fetch_cover_art, artists, album)
    except (OSError, ValueError, TimeoutError) as error:
        print(f"Cover lookup failed: {error}")
        return None

    MUSICBRAINZ_CACHE[cache_key] = cover_url
    return cover_url