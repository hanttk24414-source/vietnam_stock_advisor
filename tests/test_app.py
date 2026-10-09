"""Streamlit UI regression tests with offline, explicitly synthetic provider fixtures."""
from copy import deepcopy
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

import streamlit as st
from streamlit.testing.v1 import AppTest
from tests.fixtures import stock_fixture, prices_fixture, macro_fixture
from data.stock_loader import DataUnavailableError


class TestApp(TestCase):
    def setUp(self):
        st.cache_data.clear()
        self.addCleanup(st.cache_data.clear)
        self.patches = [
            patch('data.stock_loader.fetch_stock_list', return_value={'HPG':{'name':'Test Steel'}, 'MBB':{'name':'Test Bank'}, 'VNM':{'name':'Test Milk'}}),
            patch('data.stock_loader.fetch_stock_price_history', return_value=prices_fixture(220)),
            patch('data.stock_loader.fetch_stock_fundamentals', side_effect=self.financials),
            patch('data.macro_loader.fetch_macro_indicators', return_value=macro_fixture()),
            patch('data.macro_loader.fetch_vnindex_history', return_value=prices_fixture(220))]
        for item in self.patches:
            item.start(); self.addCleanup(item.stop)
        self.app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'), default_timeout=10)

    @staticmethod
    def financials(ticker):
        if ticker == 'VNM':
            return {'ticker':ticker, 'name':'Test Milk', 'sector':'Food', 'sector_code':'GENERAL',
                    'shares_outstanding':0, 'financial_history':[], 'data_source':'TEST FIXTURE ONLY'}
        data = deepcopy(stock_fixture('HPG'))
        data.update(ticker=ticker, name='Test '+ticker)
        return data

    def test_custom_ticker_vn_suffix_and_full_analysis(self):
        self.app.run()
        self.assertEqual(len(self.app.exception),0)
        self.app.text_input[0].set_value(' mbb.vn ').run()
        self.assertEqual(len(self.app.exception),0)
        self.assertTrue(any('MBB' in element.value for element in self.app.subheader))
        self.assertTrue(any('VNM' in option for option in self.app.selectbox[0].options))

    def test_missing_financials_shows_technical_only(self):
        self.app.run()
        self.app.text_input[0].set_value('VNM').run()
        self.assertEqual(len(self.app.exception),0)
        self.assertTrue(any('CHƯA ĐỦ' in item.value for item in self.app.info))
        self.assertEqual(len(self.app.tabs),0)

    def test_price_failure_shows_error(self):
        with patch('data.stock_loader.fetch_stock_price_history', side_effect=DataUnavailableError('Không có giá TEST')):
            self.app.run()
        self.assertEqual(len(self.app.exception),0)
        self.assertTrue(any('Không có giá' in item.value for item in self.app.error))

    def test_invalid_ticker_stops_cleanly(self):
        self.app.run()
        self.app.text_input[0].set_value('../../HPG').run()
        self.assertEqual(len(self.app.exception),0)
        self.assertTrue(self.app.error)
