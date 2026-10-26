import unittest
from unittest.mock import patch

from discord_mpris import cover_art


class FindCoverArtTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        cover_art.MUSICBRAINZ_CACHE.clear()
        cover_art.MUSICBRAINZ_LAST_REQUEST = 0.0

    @patch("discord_mpris.cover_art.fetch_cover_art", return_value=None)
    async def test_caches_a_no_cover_result(self, fetch_cover_art):
        result = await cover_art.find_cover_art(["Test Artist"], "Test Album")

        self.assertIsNone(result)
        self.assertEqual(fetch_cover_art.call_count, 1)
        self.assertIn((("test artist",), "test album"), cover_art.MUSICBRAINZ_CACHE)

    @patch(
        "discord_mpris.cover_art.fetch_cover_art",
        side_effect=OSError("MusicBrainz API request failed: timeout"),
    )
    async def test_does_not_cache_a_transient_error(self, fetch_cover_art):
        result = await cover_art.find_cover_art(["Transient Artist"], "Transient Album")

        self.assertIsNone(result)
        self.assertEqual(fetch_cover_art.call_count, 1)
        self.assertNotIn(
            (("transient artist",), "transient album"),
            cover_art.MUSICBRAINZ_CACHE,
        )


if __name__ == "__main__":
    unittest.main()