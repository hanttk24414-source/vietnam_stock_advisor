"""Offline checks for optional DNSE support."""
import os
import unittest
from unittest.mock import patch
from data.dnse_loader import dnse_configured, fetch_dnse_history


class TestDNSELoader(unittest.TestCase):
    def test_missing_credentials(self):
        with patch.dict(os.environ, {"DNSE_API_KEY": "", "DNSE_API_SECRET": ""}):
            self.assertFalse(dnse_configured())
            with self.assertRaisesRegex(RuntimeError, "DNSE_API_KEY"):
                fetch_dnse_history("HPG", 30)

    def test_stock_loader_without_dnse_does_not_crash_import(self):
        from data.stock_loader import fetch_stock_price_history
        self.assertTrue(callable(fetch_stock_price_history))


if __name__ == "__main__":
    unittest.main()
