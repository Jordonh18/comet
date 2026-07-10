import unittest

from comet.api.endpoints.chilllink import _build_chilllink_sources
from comet.api.endpoints.stream import _availability_candidates, _rank_torrents


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
    async def test_only_prefilters_torrents_with_selected_files(self):
        class TorrentManager:
            def __init__(self):
                self.torrents = {
                    "keep": {"title": "Keep", "fileIndex": 0},
                    "hydrate": {"title": "Hydrate", "fileIndex": None},
                    "drop": {"title": "Drop", "fileIndex": 1},
                }
                self.ranked_torrents = []
                self.rank_args = None
                self.rank_calls = 0

            async def rank_torrents(self, *args):
                self.rank_args = args
                self.rank_calls += 1
                self.ranked_torrents = (
                    ["keep", "missing"]
                    if self.rank_calls == 1
                    else ["keep", "hydrate"]
                )

        manager = TorrentManager()
        config = {
            "rtnSettings": "settings",
            "rtnRanking": "ranking",
            "maxSize": 50,
            "removeTrash": True,
        }

        initial_count, candidates = await _availability_candidates(manager, config)

        self.assertEqual(initial_count, 3)
        self.assertEqual(
            candidates,
            {
                "keep": {"title": "Keep", "fileIndex": 0},
                "hydrate": {"title": "Hydrate", "fileIndex": None},
            },
        )
        self.assertEqual(
            manager.rank_args,
            ("settings", "ranking", 0, 50, True),
        )

        candidates["hydrate"]["fileIndex"] = 2
        await _rank_torrents(manager, config)

        self.assertEqual(manager.rank_calls, 2)
        self.assertEqual(manager.ranked_torrents, ["keep", "hydrate"])


if __name__ == "__main__":
    unittest.main()
