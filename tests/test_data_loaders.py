"""Offline provider, isolation, error handling and ticker regression tests."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

from data import stock_loader as loader
from data.industry_loader import get_industry_analysis
from data.vietcap_provider import normalize_statements, sector_code
from tests.fixtures import prices_fixture, stock_fixture


class TestDataLoaders(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cache_patch = patch.object(loader, 'CACHE_DIR', Path(self.temp.name))
        self.cache_patch.start()
        self.addCleanup(self.cache_patch.stop)

    def test_clean_and_reject_ticker(self):
        self.assertEqual(loader.clean_ticker(' mbb.vn '), 'MBB')
        for bad in ['../../HPG', 'FPT<script>', 'HPG.VN.VN', '', 'AA']:
            with self.assertRaises(ValueError):
                loader.clean_ticker(bad)

    def test_live_arbitrary_ticker_and_cache(self):
        with patch.object(loader.vci, 'history', return_value=prices_fixture(80)) as provider:
            frame = loader.fetch_stock_price_history('MBB.VN', 120)
        provider.assert_called_once_with('MBB', 120)
        self.assertEqual(frame.attrs['ticker'], 'MBB')
        self.assertEqual(frame.attrs['data_source'], 'Vietcap')
        self.assertTrue((Path(self.temp.name)/'MBB_prices_v2.json').exists())

    @patch.object(loader.yf, 'Ticker', side_effect=OSError('offline'))
    @patch.object(loader.requests, 'get', side_effect=OSError('offline'))
    @patch.object(loader.vci, 'history', side_effect=OSError('offline'))
    def test_no_random_prices_on_failure(self, *_):
        with self.assertRaises(loader.DataUnavailableError):
            loader.fetch_stock_price_history('ZZZ', 365)

    def test_prices_cache_same_ticker_only(self):
        with patch.object(loader.vci, 'history', return_value=prices_fixture(80)):
            original = loader.fetch_stock_price_history('VNM', 120)
        with patch.object(loader.vci, 'history', side_effect=OSError()), patch.object(loader.requests, 'get', side_effect=OSError()), patch.object(loader.yf, 'Ticker', side_effect=OSError()):
            cached = loader.fetch_stock_price_history('VNM', 120)
            self.assertTrue(cached.attrs['cached'])
            self.assertAlmostEqual(original.close.iloc[-1], cached.close.iloc[-1], places=6)
            with self.assertRaises(loader.DataUnavailableError):
                loader.fetch_stock_price_history('MBB', 120)

    def test_arbitrary_financials_are_not_hpg(self):
        financials = stock_fixture('FPT'); financials.update(ticker='MBB', name='Test Bank', data_source='Vietcap')
        with patch.object(loader.vci, 'fundamentals', return_value=financials):
            actual = loader.fetch_stock_fundamentals('MBB')
        self.assertEqual(actual['name'], 'Test Bank')
        self.assertEqual(actual['ticker'], 'MBB')
        self.assertEqual(actual['financial_history'], financials['financial_history'])

    def test_missing_financials_and_legacy_cache_never_use_presets(self):
        (Path(self.temp.name)/'ZZZ_fundamentals.json').write_text(json.dumps(stock_fixture('HPG')))
        with patch.object(loader.vci, 'fundamentals', return_value={}), patch.object(loader, '_yahoo_fundamentals', return_value={}):
            actual = loader.fetch_stock_fundamentals('ZZZ')
        self.assertEqual(actual['financial_history'], [])
        self.assertEqual(loader.get_preset_fundamentals('ZZZ'), {})
        self.assertEqual(actual['shares_outstanding'], 0)

    def test_financial_cache_preserves_source_and_date(self):
        financials = stock_fixture('FPT'); financials.update(ticker='VNM', data_source='Vietcap', last_updated='2026-10-01')
        with patch.object(loader.vci, 'fundamentals', return_value=financials):
            loader.fetch_stock_fundamentals('VNM')
        with patch.object(loader.vci, 'fundamentals', return_value={}), patch.object(loader, '_yahoo_fundamentals', return_value={}):
            cached = loader.fetch_stock_fundamentals('VNM')
        self.assertTrue(cached['cached'])
        self.assertEqual(cached['last_updated'], '2026-10-01')

    def test_unknown_industry_not_steel(self):
        result = get_industry_analysis('FOOD')
        self.assertEqual(result['benchmark_pe'], 0)
        self.assertEqual(result['peers'], [])

    def test_sector_from_actual_company(self):
        self.assertEqual(sector_code('Ngân hàng'), 'BANKING')
        self.assertEqual(sector_code('Food production'), 'GENERAL')

    def test_statement_mapping_joins_years_and_retains_missing(self):
        metadata = {'income': [{'field': 'a', 'titleEn': 'Net sales'}, {'field':'b', 'titleEn':'Net profit'}],
                    'balance': [{'field':'c', 'titleEn':'Total assets'}, {'field':'d', 'titleEn':"Owners equity"}]}
        sections = [{'years':[{'yearReport':2025, 'a':12e9, 'b':2e9}, {'yearReport':2024, 'a':10e9, 'b':1e9}]},
                    {'years':[{'yearReport':2024, 'c':20e9, 'd':8e9}, {'yearReport':2025, 'c':25e9, 'd':10e9}]}]
        result = normalize_statements(metadata, sections)
        self.assertEqual(result[0]['year'], '2024')
        self.assertEqual(result[1]['equity'], 10)
        self.assertNotIn('capex', result[1])
        self.assertNotIn('fcf', result[1])

    def test_listing_uses_all_provider_symbols(self):
        with patch.object(loader.vci, 'listings', return_value={'MBB': {'name':'Bank'}, 'VNM': {'name':'Milk'}}):
            self.assertEqual(set(loader.fetch_stock_list()), {'MBB', 'VNM'})

    def test_vietcap_history_keeps_vnd_units(self):
        from data import vietcap_provider as provider
        from datetime import datetime
        timestamp = int(datetime.now().timestamp())
        response = Mock()
        response.json.return_value = [{'symbol':'MBB', 't':[timestamp],
            'o':[700], 'h':[710], 'l':[690], 'c':[705], 'v':[1000]}]
        with patch.object(provider.requests, 'post', return_value=response):
            result = provider.history('MBB',365)
        self.assertEqual(result.close.iloc[0],705)

    def test_sync_price_used_for_valuation(self):
        result = loader.sync_market_price(stock_fixture('HPG'), prices_fixture(80))
        self.assertAlmostEqual(result['current_price'], prices_fixture(80).close.iloc[-1])
        self.assertGreater(result['pe'],0)

    def test_vietcap_company_and_statements_contract(self):
        from data import vietcap_provider as provider
        labels = {'a':'Net sales', 'b':'Net profit', 'c':'Total assets', 'd':"Owners equity"}
        metadata = {'income':[{'field':k, 'titleEn':v} for k,v in labels.items()]}
        responses = [
            {'data':{'ticker':'MBB', 'viOrganName':'Test Bank', 'sectorVn':'Ngân hàng', 'numberOfSharesMktCap':1000000000}},
            {'data':metadata},
            {'data':{'years':[{'yearReport':2025, 'a':2e9, 'b':1e9}, {'yearReport':2024, 'a':1e9, 'b':.5e9}]}},
            {'data':{'years':[{'yearReport':2025, 'c':10e9, 'd':5e9}, {'yearReport':2024, 'c':9e9, 'd':4e9}]}},
            {'data':{'years':[]}}]
        with patch.object(provider, '_get', side_effect=responses):
            result = provider.fundamentals('MBB')
        self.assertEqual(result['sector_code'],'BANKING')
        self.assertEqual(result['shares_outstanding'],1000000000)
        self.assertEqual(result['financial_history'][-1]['revenue'],2)

    def test_dnse_priority_is_preserved(self):
        with patch.object(loader, 'dnse_configured', return_value=True), patch.object(loader, 'fetch_dnse_history', return_value=prices_fixture(80)), patch.object(loader.vci, 'history') as vietcap:
            result = loader.fetch_stock_price_history('MBB', 120)
        self.assertEqual(result.attrs['data_source'], 'DNSE OpenAPI')
        vietcap.assert_not_called()
