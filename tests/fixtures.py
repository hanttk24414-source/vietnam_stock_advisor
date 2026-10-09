"""Explicitly synthetic fixtures; never used by production data loaders."""
from copy import deepcopy
import numpy as np
import pandas as pd
from config import SUPPORTED_TICKERS
from data.stock_loader import get_preset_fundamentals
from data.macro_loader import DEFAULT_MACRO_FACTS


def stock_fixture(ticker='HPG'):
    data = {**deepcopy(SUPPORTED_TICKERS[ticker]), **deepcopy(get_preset_fundamentals(ticker))}
    data.update(ticker=ticker, data_source='TEST FIXTURE ONLY')
    return data


def prices_fixture(days=120):
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=days)
    close = 25000 + np.arange(days)*25 + np.sin(np.arange(days)*.7)*450
    frame = pd.DataFrame({'open': close-50, 'high': close+150, 'low': close-150,
                          'close': close, 'volume': np.full(days, 1000000)}, index=dates)
    frame.index.name = 'date'
    frame.attrs.update(data_source='TEST FIXTURE ONLY', price_as_of=dates[-1].strftime('%Y-%m-%d'))
    return frame


def macro_fixture():
    return {**DEFAULT_MACRO_FACTS, 'usd_vnd_rate': 25000, 'vnindex_current': 1200,
            'equity_risk_premium': 9.3}
