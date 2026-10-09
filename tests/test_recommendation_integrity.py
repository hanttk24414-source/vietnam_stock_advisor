"""Regression tests for user-entered symbols and recommendation differentiation."""
import os
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from data.industry_loader import get_industry_analysis
from data.stock_loader import infer_sector_code, fetch_stock_fundamentals, fetch_stock_price_history, DataUnavailableError
from analytics.scorecard_engine import calculate_quant_scorecard


class RecommendationIntegrityTests(unittest.TestCase):
    def test_unknown_sector_is_not_steel(self):
        self.assertEqual(get_industry_analysis("GENERAL")["benchmark_pe"], 0.0)
        self.assertEqual(get_industry_analysis("GENERAL")["peers"], [])

    def test_dynamic_sector_mapping(self):
        self.assertEqual(infer_sector_code({"sector": "Financial Services", "industry": "Banks - Regional"}), "BANKING")
        self.assertEqual(infer_sector_code({"sector": "Technology", "industry": "Software - Application"}), "TECH")
        self.assertEqual(infer_sector_code({}), "GENERAL")

    def test_unknown_ticker_cannot_fall_back_to_hpg(self):
        with tempfile.TemporaryDirectory() as directory, patch('data.stock_loader.CACHE_DIR', Path(directory)):
            with patch('data.stock_loader.vci.fundamentals', return_value={}):
                with patch("data.stock_loader.yf.Ticker", side_effect=RuntimeError("offline")):
                    result = fetch_stock_fundamentals("ZZZZ")
        self.assertEqual(result['ticker'], 'ZZZZ')
        self.assertEqual(result['financial_history'], [])

    def test_offline_live_price_cannot_be_synthetic(self):
        with tempfile.TemporaryDirectory() as directory, patch('data.stock_loader.CACHE_DIR', Path(directory)):
            with patch('data.stock_loader.dnse_configured', return_value=False), patch('data.stock_loader.vci.history', side_effect=RuntimeError('offline')):
                with patch("data.stock_loader.requests.get", side_effect=RuntimeError("offline")):
                    with patch("data.stock_loader.yf.Ticker", side_effect=RuntimeError("offline")):
                        with self.assertRaises(DataUnavailableError):
                            fetch_stock_price_history("ZZZZ", 30)

    def test_recommendations_use_stock_specific_evidence(self):
        common = {
            "fundamental_analysis": {
                "available": True, "ticker": "FPT", "rev_growth_yoy": 14, "ni_growth_yoy": 12, "rev_cagr_3y": 10,
                "roe": 18, "roa": 8, "net_margin": 9, "cf_quality_score": 70,
                "ocf_to_ni_ratio": 0.8, "debt_to_equity": 0.7, "health_score": 75,
            },
            "industry_analysis": {"pe_discount_pct": 4},
            "macro_analysis": {"equity_risk_premium": 2},
        }
        bullish = calculate_quant_scorecard(
            **common, technical_analysis={"current_price":20000, "sma20":19000, "sma50":18000, "tech_score": 85, "rsi": 55, "overall_signal": "TÍCH CỰC (BULLISH)"},
            valuation_analysis={"available":True, "blended_target_price":26000, "blended_upside": 30},
        )
        bearish = calculate_quant_scorecard(
            **common, technical_analysis={"current_price":20000, "sma20":21000, "sma50":22000, "tech_score": 25, "rsi": 26, "overall_signal": "TIÊU CỰC (BEARISH)"},
            valuation_analysis={"available":True, "blended_target_price":16400, "blended_upside": -18},
        )
        self.assertNotEqual(bullish["summary"], bearish["summary"])
        self.assertIn("RSI 55.0", bullish["summary"])
        self.assertIn("RSI 26.0", bearish["summary"])


if __name__ == "__main__":
    unittest.main()

