"""Regression tests: live mode must never substitute synthetic financial data."""
import os
import unittest
from unittest.mock import patch

import pandas as pd

from data.macro_loader import fetch_macro_indicators, fetch_vnindex_history
from data.stock_loader import fetch_stock_price_history, fetch_stock_fundamentals


class LiveDataIntegrityTests(unittest.TestCase):
    def test_macro_requires_verified_inputs(self):
        with patch.dict(os.environ, {"STOCK_ADVISOR_DEMO": "0"}):
            with self.assertRaisesRegex(RuntimeError, "vĩ mô"):
                fetch_macro_indicators()

    def test_stock_price_api_failure_does_not_generate_random_prices(self):
        with patch.dict(os.environ, {"STOCK_ADVISOR_DEMO": "0"}, clear=False):
            with patch("data.stock_loader.dnse_configured", return_value=False), \
                 patch("data.stock_loader.requests.get", side_effect=ConnectionError("offline")), \
                 patch("data.stock_loader.yf.Ticker", side_effect=ConnectionError("offline")):
                with self.assertRaisesRegex(RuntimeError, "Không thể lấy giá THẬT"):
                    fetch_stock_price_history("HPG", 45)

    def test_financial_api_failure_does_not_return_sample_statements(self):
        with patch.dict(os.environ, {"STOCK_ADVISOR_DEMO": "0"}):
            with patch("data.stock_loader.yf.Ticker", side_effect=ConnectionError("offline")):
                with self.assertRaisesRegex(RuntimeError, "BCTC"):
                    fetch_stock_fundamentals("HPG")

    def test_vnindex_api_failure_does_not_generate_random_index(self):
        with patch.dict(os.environ, {"STOCK_ADVISOR_DEMO": "0"}):
            with patch("data.macro_loader.requests.get", side_effect=ConnectionError("offline")):
                with self.assertRaisesRegex(RuntimeError, "VN-Index"):
                    fetch_vnindex_history(30)


if __name__ == "__main__":
    unittest.main()
