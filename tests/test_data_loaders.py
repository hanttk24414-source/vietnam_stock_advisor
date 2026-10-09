"""
Unit tests kiểm tra các module thu thập và nạp dữ liệu.
"""

import unittest
import pandas as pd
from data.macro_loader import fetch_macro_indicators, fetch_vnindex_history
from data.industry_loader import get_industry_analysis, get_all_industries
from data.stock_loader import fetch_stock_price_history, fetch_stock_fundamentals, clean_ticker

class TestDataLoaders(unittest.TestCase):

    def test_clean_ticker(self):
        self.assertEqual(clean_ticker("HPG.VN"), "HPG")
        self.assertEqual(clean_ticker(" fpt "), "FPT")
        self.assertEqual(clean_ticker("VCB"), "VCB")

    def test_macro_loader(self):
        macro = fetch_macro_indicators()
        self.assertIsInstance(macro, dict)
        self.assertIn("gdp_growth_latest_quarter", macro)
        self.assertIn("cpi_yoy", macro)
        self.assertIn("refinancing_rate", macro)
        self.assertIn("usd_vnd_rate", macro)
        self.assertIn("equity_risk_premium", macro)
        self.assertGreater(macro["usd_vnd_rate"], 20000)

    def test_vnindex_history(self):
        df = fetch_vnindex_history(days=30)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        for col in ["open", "high", "low", "close", "volume"]:
            self.assertIn(col, df.columns)

    def test_industry_loader(self):
        ind = get_industry_analysis("STEEL")
        self.assertIn("name", ind)
        self.assertIn("drivers", ind)
        self.assertIn("risks", ind)
        self.assertIn("peers", ind)
        self.assertGreater(len(ind["peers"]), 0)

        all_ind = get_all_industries()
        self.assertIn("STEEL", all_ind)
        self.assertIn("TECH", all_ind)
        self.assertIn("BANKING", all_ind)

    def test_stock_price_loader(self):
        df = fetch_stock_price_history("HPG", days=60)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        self.assertGreater(len(df), 20)
        self.assertIn("close", df.columns)
        self.assertGreater(df["close"].iloc[-1], 1000)

    def test_stock_fundamentals_loader(self):
        fund = fetch_stock_fundamentals("HPG")
        self.assertIsInstance(fund, dict)
        self.assertEqual(fund.get("ticker"), "HPG")
        self.assertIn("financial_history", fund)
        self.assertGreaterEqual(len(fund["financial_history"]), 3)
        self.assertGreater(fund["financial_history"][-1]["revenue"], 0)

if __name__ == "__main__":
    unittest.main()
