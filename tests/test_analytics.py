"""
Unit tests kiểm tra các thuật toán phân tích kỹ thuật, cơ bản, định giá và chấm điểm.
"""

import unittest
import os
import numpy as np
import pandas as pd
from analytics.macro_engine import analyze_macro_environment
from analytics.industry_engine import evaluate_industry_and_peers
from analytics.technical_engine import compute_technical_indicators
from analytics.fundamental_engine import analyze_fundamentals
from analytics.valuation_engine import perform_valuation
from analytics.scorecard_engine import calculate_quant_scorecard, build_scenario_matrix
from data.macro_loader import fetch_macro_indicators
from data.stock_loader import fetch_stock_fundamentals, fetch_stock_price_history

class TestAnalytics(unittest.TestCase):

    def setUp(self):
        os.environ['STOCK_ADVISOR_DEMO'] = '1'
        self.macro_raw = fetch_macro_indicators()
        self.stock_raw = fetch_stock_fundamentals("HPG")
        self.price_df = fetch_stock_price_history("HPG", 120)

    def test_macro_engine(self):
        macro_res = analyze_macro_environment(self.macro_raw)
        self.assertIn("cycle_stage", macro_res)
        self.assertIn("monetary_stance", macro_res)
        self.assertIn("equity_risk_premium", macro_res)
        self.assertGreater(macro_res["equity_risk_premium"], 0.0)

    def test_technical_engine(self):
        tech_res = compute_technical_indicators(self.price_df)
        self.assertIn("rsi", tech_res)
        self.assertIn("macd", tech_res)
        self.assertIn("sma20", tech_res)
        self.assertIn("sma50", tech_res)
        self.assertIn("sharpe_ratio", tech_res)
        self.assertIn("annualized_volatility_pct", tech_res)
        self.assertGreater(tech_res["rsi"], 0.0)
        self.assertLess(tech_res["rsi"], 100.0)

    def test_fundamental_engine(self):
        fund_res = analyze_fundamentals(self.stock_raw)
        self.assertIn("roe", fund_res)
        self.assertIn("net_margin", fund_res)
        self.assertIn("asset_turnover", fund_res)
        self.assertIn("equity_multiplier", fund_res)
        self.assertIn("debt_to_equity", fund_res)
        self.assertIn("fcf_bil", fund_res)
        self.assertGreater(fund_res["roe"], 0.0)
        # Kiểm tra tính đồng bộ của DuPont: ROE xấp xỉ Margin * Turnover * Multiplier
        calc_roe = fund_res["net_margin"] * fund_res["asset_turnover"] * fund_res["equity_multiplier"]
        self.assertAlmostEqual(fund_res["roe"], calc_roe, delta=3.0)

    def test_valuation_engine(self):
        fund_res = analyze_fundamentals(self.stock_raw)
        ind_res = evaluate_industry_and_peers("STEEL", self.stock_raw)
        val_res = perform_valuation(self.stock_raw, fund_res, ind_res, beta=1.1)
        self.assertIn("pe_fair_value", val_res)
        self.assertIn("pb_fair_value", val_res)
        self.assertIn("dcf_fair_value", val_res)
        self.assertIn("blended_target_price", val_res)
        self.assertGreater(val_res["blended_target_price"], 0)
        self.assertGreater(val_res["dcf_fair_value"], 0)

    def test_scorecard_and_scenarios(self):
        fund_res = analyze_fundamentals(self.stock_raw)
        ind_res = evaluate_industry_and_peers("STEEL", self.stock_raw)
        tech_res = compute_technical_indicators(self.price_df)
        val_res = perform_valuation(self.stock_raw, fund_res, ind_res, beta=1.1)
        macro_res = analyze_macro_environment(self.macro_raw)
        
        score_res = calculate_quant_scorecard(fund_res, tech_res, val_res, ind_res, macro_res)
        self.assertIn("total_score", score_res)
        self.assertIn("rating", score_res)
        self.assertGreaterEqual(score_res["total_score"], 0)
        self.assertLessEqual(score_res["total_score"], 100)

        scen_res = build_scenario_matrix(val_res["current_price"], val_res["blended_target_price"], fund_res, tech_res)
        self.assertIn("bull_case", scen_res)
        self.assertIn("base_case", scen_res)
        self.assertIn("bear_case", scen_res)
        bull_p = scen_res["bull_case"]["target_price"]
        base_p = scen_res["base_case"]["target_price"]
        bear_p = scen_res["bear_case"]["target_price"]
        # Kịch bản Bull phải lớn hơn Base, Base phải lớn hơn Bear
        self.assertGreater(bull_p, base_p)
        self.assertGreater(base_p, bear_p)

if __name__ == "__main__":
    unittest.main()
