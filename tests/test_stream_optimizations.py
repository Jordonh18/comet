import unittest

from comet.api.endpoints.chilllink import _build_chilllink_sources
from comet.api.endpoints.stream import _availability_candidates


class ChillLinkSourceTests(unittest.TestCase):
    def test_keeps_standard_stream_fields(self):
        streams = [
            {
                "behaviorHints": {
                    "bingeGroup": "comet.fast.1080p",
                    "filename": "Movie.1080p.mkv",
                },
                "url": "https://example.com/movie",
                "_chilllink": [{"quality": "1080p"}],
            }
        ]

        self.assertEqual(
            _build_chilllink_sources(streams),
            [
                {
                    "id": "comet.fast.1080p",
                    "title": "Movie.1080p.mkv",
                    "url": "https://example.com/movie",
                    "metadata": [{"quality": "1080p"}],
                }
            ],
        )

    def test_handles_streams_without_behavior_hints(self):
        streams = [
            {"title": "Missing URL"},
            {
                "name": "Fallback title",
                "externalUrl": "https://example.com/fallback",
            },
        ]

        self.assertEqual(
            _build_chilllink_sources(streams),
            [
                {
                    "id": "comet.fast.1",
                    "title": "Fallback title",
                    "url": "https://example.com/fallback",
                    "metadata": [],
                }
            ],
        )


class AvailabilityCandidateTests(unittest.IsolatedAsyncioTestCase):
    async def test_filters_before_debrid_availability_checks(self):
        class TorrentManager:
            def __init__(self):
                self.torrents = {
                    "keep": {"title": "Keep"},
                    "drop": {"title": "Drop"},
                }
                self.ranked_torrents = []
                self.rank_args = None

            async def rank_torrents(self, *args):
                self.rank_args = args
                self.ranked_torrents = ["keep", "missing"]

        manager = TorrentManager()
        config = {
            "rtnSettings": "settings",
            "rtnRanking": "ranking",
            "maxSize": 50,
            "removeTrash": True,
        }

        initial_count, candidates = await _availability_candidates(manager, config)

        self.assertEqual(initial_count, 2)
        self.assertEqual(candidates, {"keep": {"title": "Keep"}})
        self.assertEqual(
            manager.rank_args,
            ("settings", "ranking", 0, 50, True),
        )


if __name__ == "__main__":
    unittest.main()
