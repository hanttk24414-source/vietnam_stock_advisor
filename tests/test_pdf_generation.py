"""
Unit tests kiểm tra việc tạo báo cáo PDF hoàn chỉnh.
"""

import os
import unittest
from pathlib import Path
from data.macro_loader import fetch_macro_indicators, fetch_vnindex_history
from tests.fixtures import stock_fixture, prices_fixture, macro_fixture
from analytics.macro_engine import analyze_macro_environment
from analytics.industry_engine import evaluate_industry_and_peers
from analytics.technical_engine import compute_technical_indicators
from analytics.fundamental_engine import analyze_fundamentals
from analytics.valuation_engine import perform_valuation
from analytics.scorecard_engine import calculate_quant_scorecard, build_scenario_matrix
from reporting.pdf_generator import create_investment_report_pdf

class TestPDFGeneration(unittest.TestCase):

    def test_pdf_generation_flow(self):
        sym = "HPG"
        macro_raw = macro_fixture()
        vn_df = prices_fixture(120)
        macro_res = analyze_macro_environment(macro_raw)
        
        price_df = prices_fixture(120)
        stock_raw = stock_fixture(sym)
        tech_res = compute_technical_indicators(price_df, vn_df)
        fund_res = analyze_fundamentals(stock_raw)
        ind_res = evaluate_industry_and_peers("STEEL", stock_raw)
        val_res = perform_valuation(stock_raw, fund_res, ind_res, beta=1.1)
        score_res = calculate_quant_scorecard(fund_res, tech_res, val_res, ind_res, macro_res)
        scen_res = build_scenario_matrix(val_res["current_price"], val_res["blended_target_price"], fund_res, tech_res)

        test_pdf_name = "test_unit_report.pdf"
        pdf_path = create_investment_report_pdf(
            ticker=sym,
            stock_fundamentals=stock_raw,
            fundamental_analysis=fund_res,
            technical_analysis=tech_res,
            valuation_analysis=val_res,
            scorecard_analysis=score_res,
            scenario_analysis=scen_res,
            macro_analysis=macro_res,
            industry_analysis=ind_res,
            price_df=price_df,
            output_filename=test_pdf_name
        )

        self.assertTrue(os.path.exists(pdf_path))
        self.assertGreater(os.path.getsize(pdf_path), 50_000) # Lớn hơn 50KB

        # Dọn dẹp file test
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

if __name__ == "__main__":
    unittest.main()

