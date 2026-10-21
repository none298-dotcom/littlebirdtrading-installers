"""Fixture contract tests only. No production app source or credentials."""
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from server import payload

MARKETS = json.loads(Path(__file__).with_name("markets.json").read_text())
NOW = datetime(2026, 10, 21, 14, 0, tzinfo=timezone.utc)


class FixtureTests(unittest.TestCase):
    def test_two_lists_and_all_symbols(self):
        self.assertEqual([m["code"] for m in MARKETS], ["US", "AT"])
        self.assertEqual(MARKETS[0]["symbols"], ["spy", "es", "qqq", "nq"])
        expected = "nvda tsla btc eth gld slv cl gc amd mstr aapl pltr coin amzn meta msft smci hood mara gme ibit etha intc rivn".split()
        self.assertEqual(MARKETS[1]["symbols"], expected)

    def test_schedule_uses_one_clock(self):
        body, code = payload("/api/app/next", MARKETS, NOW)
        self.assertEqual(code, 200)
        self.assertEqual([m["market"] for m in body["markets"]], ["US", "AT"])
        self.assertTrue(body["markets"][0]["freeAt"] < body["now"] < body["markets"][1]["freeAt"])

    def test_four_index_symbols_open(self):
        body, code = payload("/api/app/levels/US", MARKETS, NOW)
        self.assertEqual(code, 200)
        self.assertEqual(body["access"], "free")
        self.assertEqual(list(body["symbols"]), ["SPY", "ES", "QQQ", "NQ"])
        self.assertTrue(all(len(s["lines"]) == 3 for s in body["symbols"].values()))
        self.assertEqual(body["report"]["date"], "2026-10-21")

    def test_locked_active_never_exposes_levels(self):
        body, code = payload("/api/app/levels/AT", MARKETS, NOW)
        self.assertEqual(code, 200)
        self.assertEqual(body["access"], "locked")
        self.assertFalse(body["pro"])
        self.assertNotIn("symbols", body)
        self.assertNotIn("charts", body)

    def test_unknown_list_rejected(self):
        self.assertEqual(payload("/api/app/levels/JP", MARKETS, NOW)[1], 404)

    def test_exact_routes_and_query(self):
        self.assertEqual(payload("/api/app/markets?fixture=1", MARKETS, NOW)[1], 200)
        self.assertEqual(payload("/not/api/app/markets", MARKETS, NOW)[1], 404)

    def test_signed_out_and_free_sync(self):
        self.assertEqual(payload("/api/app/me", MARKETS, NOW)[1], 401)
        self.assertEqual(payload("/api/app/sync", MARKETS, NOW)[1], 403)


if __name__ == "__main__":
    unittest.main()
