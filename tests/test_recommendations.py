import unittest
from copy import deepcopy
from analytics.recommendation_engine import build_recommendation
from analytics.fundamental_engine import analyze_fundamentals
from analytics.scorecard_engine import calculate_quant_scorecard, build_scenario_matrix
from analytics.technical_engine import compute_technical_indicators
from analytics.valuation_engine import perform_valuation
from analytics.industry_engine import evaluate_industry_and_peers
from tests.fixtures import stock_fixture, prices_fixture


class TestRecommendations(unittest.TestCase):
    def setUp(self):
        self.tech = {'current_price':30000, 'sma20':29000, 'sma50':28000,
                     'rsi':55, 'macd_hist':120, 'vol_surge_ratio':1.3,
                     'support_levels':[27000,28000], 'resistance_levels':[32000,35000], 'atr14':500}
        self.fund = {'available':True, 'period':'2024 → 2025', 'ni_growth_yoy':25,
                     'rev_growth_yoy':20, 'roe':23, 'missing_fields':[]}
        self.val = {'available':True, 'blended_target_price':39000, 'blended_upside':30}

    def test_different_facts_change_rating_and_thesis(self):
        strong = build_recommendation('MBB', self.tech, self.fund, self.val, 85)
        weak_tech = {**self.tech, 'current_price':25000, 'rsi':32}
        weak_fund = {**self.fund, 'ni_growth_yoy':-35}
        weak_val = {**self.val, 'blended_upside':-15, 'blended_target_price':21250}
        weak = build_recommendation('VNM', weak_tech, weak_fund, weak_val, 32)
        self.assertIn('MUA MẠNH', strong['rating'])
        self.assertIn('GIẢM TỶ TRỌNG', weak['rating'])
        self.assertNotEqual(strong['summary'], weak['summary'])
        self.assertIn('-35.0%', weak['summary'])
        self.assertIn('MBB', strong['action_guide'])

    def test_same_inputs_same_output(self):
        self.assertEqual(build_recommendation('MBB', self.tech, self.fund, self.val, 85),
                         build_recommendation('MBB', self.tech, self.fund, self.val, 85))

    def test_overbought_high_score_not_buy(self):
        result = build_recommendation('MBB', {**self.tech, 'rsi':82}, self.fund, self.val, 90)
        self.assertNotIn('MUA', result['rating'])
        self.assertIn('quá mua', result['action_guide'])

    def test_bearish_high_score_not_buy(self):
        result = build_recommendation('MBB', {**self.tech, 'current_price':26000}, self.fund, self.val, 95)
        self.assertNotIn('MUA', result['rating'])

    def test_missing_financials_no_defaults(self):
        fund = analyze_fundamentals({'ticker':'VNM', 'financial_history':[]})
        self.assertFalse(fund['available'])
        self.assertNotIn('fcf_bil', fund)
        result = calculate_quant_scorecard(fund, self.tech, {}, {}, {})
        self.assertIsNone(result['total_score'])
        self.assertIn('CHƯA ĐỦ', result['rating'])

    def test_stale_prices_override_buy(self):
        result = build_recommendation('MBB', self.tech, self.fund, self.val, 90,
                                      {'stale':True, 'price_as_of':'2020-01-01'})
        self.assertIn('CHƯA KHUYẾN NGHỊ', result['rating'])
        self.assertIn('2020-01-01', result['action_guide'])

    def test_missing_cashflow_blocks_aggregate_score(self):
        raw = stock_fixture(); del raw['financial_history'][-1]['ocf']
        fund = analyze_fundamentals(raw)
        result = calculate_quant_scorecard(fund, self.tech, self.val, {}, {})
        self.assertIsNone(result['total_score'])
        self.assertIn('ocf', ' '.join(result['risks']))

    def test_negative_fcf_never_manufactures_positive_dcf(self):
        raw = stock_fixture(); fund = analyze_fundamentals(raw)
        fund.update(fcf_bil=-1000, ocf_bil=-2000)
        result = perform_valuation(raw, fund, evaluate_industry_and_peers('STEEL', raw))
        self.assertFalse(result['dcf_available'])
        self.assertEqual(result['dcf_fair_value'], 0)
        self.assertEqual(result['method_weights']['dcf'], 0)

    def test_rsi_all_up_equals_100(self):
        frame = prices_fixture(80)
        frame['close'] = range(10000,10080)
        self.assertEqual(compute_technical_indicators(frame)['rsi'],100)

    def test_scenarios_order_even_when_overpriced(self):
        result = build_scenario_matrix(30000, 15000, self.fund, self.tech)
        self.assertLess(result['bear_case']['target_price'], result['base_case']['target_price'])
        self.assertIn('giả định', result['assumption_notice'])
