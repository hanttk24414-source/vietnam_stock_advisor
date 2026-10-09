"""Ticker-specific live data and provenance-aware offline cache.
Sample financials are available only through get_preset_fundamentals for tests.
"""
import json
import re
import time
from datetime import datetime, timedelta
from typing import Dict, Any

import numpy as np
import pandas as pd
import requests
import yfinance as yf

from config import CACHE_DIR, SUPPORTED_TICKERS
from data import vietcap_provider as vci
from data.dnse_loader import dnse_configured, fetch_dnse_history

def infer_sector_code(info: dict) -> str:
    """Map Yahoo sector/industry labels to one of the locally supported sectors."""
    sector = str(info.get('sector') or '').lower()
    industry = str(info.get('industry') or '').lower()
    if any(x in industry for x in ('bank', 'credit services')) or 'bank' in sector:
        return 'BANKING'
    if any(x in industry for x in ('capital markets', 'asset management', 'brokerage')):
        return 'BROKERAGE'
    if any(x in industry for x in ('steel', 'metal fabrication')) or 'steel' in sector:
        return 'STEEL'
    if any(x in industry for x in ('software', 'information technology services', 'semiconductors')):
        return 'TECH'
    if 'technology' in sector and 'hardware' not in industry:
        return 'TECH'
    if any(x in industry for x in ('real estate development', 'residential construction')):
        return 'REAL_ESTATE'
    if any(x in industry for x in ('specialty retail', 'grocery stores', 'department stores', 'consumer electronics')):
        return 'RETAIL'
    return 'GENERAL'




class DataUnavailableError(ValueError):
    pass


def clean_ticker(ticker: str) -> str:
    symbol = ticker.strip().upper()
    if symbol.endswith('.VN'):
        symbol = symbol[:-3]
    if not re.fullmatch(r'[A-Z][A-Z0-9]{2,5}', symbol):
        raise ValueError('Mã cổ phiếu gồm 3–6 chữ cái/số, ví dụ MBB, VNM hoặc FPT.VN.')
    return symbol


def fetch_stock_list() -> Dict[str, Any]:
    cache = CACHE_DIR / 'listed_stocks_v2.json'
    try:
        result = vci.listings()
        if result:
            _write(cache, result)
            return result
    except Exception:
        pass
    try:
        return json.loads(cache.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {s: {'name': m['name'], 'exchange': m['exchange']}
                for s, m in SUPPORTED_TICKERS.items()}


def _write(path, data):
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    except (OSError, ValueError):
        pass


def _normalize_prices(frame, symbol, days, source, cached=False):
    required = ['open', 'high', 'low', 'close', 'volume']
    frame = frame[required].apply(pd.to_numeric, errors='coerce').dropna()
    frame.index = pd.to_datetime(frame.index)
    if frame.index.tz is not None:
        frame.index = frame.index.tz_localize(None)
    frame.index = frame.index.normalize()
    frame = frame.sort_index().loc[lambda df: ~df.index.duplicated(keep='last')]
    frame = frame.loc[(frame[['open', 'high', 'low', 'close']] > 0).all(axis=1) & (frame.volume >= 0)]
    cutoff = pd.Timestamp(datetime.now().date() - timedelta(days=days))
    frame = frame.loc[(frame.index >= cutoff) & (frame.index <= pd.Timestamp(datetime.now().date()))]
    if frame.empty:
        raise DataUnavailableError(f'Không có giá hợp lệ của {symbol} trong khoảng đã chọn.')
    frame.index.name = 'date'
    age = (datetime.now().date() - frame.index[-1].date()).days
    frame.attrs.update(ticker=symbol, data_source=source, cached=cached,
                       price_as_of=frame.index[-1].strftime('%Y-%m-%d'), stale=age > 7)
    return frame


def fetch_stock_price_history(ticker: str, days: int = 365) -> pd.DataFrame:
    symbol = clean_ticker(ticker)
    cache = CACHE_DIR / f'{symbol}_prices_v2.json'
    errors = []
    def finish(frame, source):
        frame = _normalize_prices(frame, symbol, days, source)
        _write(cache, {'ticker': symbol, 'source': source,
                      'rows': json.loads(frame.reset_index().to_json(orient='records', date_format='iso'))})
        return frame
    if dnse_configured():
        try:
            return finish(fetch_dnse_history(symbol, days), 'DNSE OpenAPI')
        except Exception as exc:
            errors.append(str(exc))
    try:
        return finish(vci.history(symbol, days), 'Vietcap')
    except Exception as exc:
        errors.append(str(exc))
    try:
        now = int(time.time())
        response = requests.get('https://dchart-api.vndirect.com.vn/dchart/history',
            params={'resolution': 'D', 'symbol': symbol, 'from': now-days*86400, 'to': now},
            headers={'User-Agent': 'Mozilla/5.0'}, timeout=7)
        response.raise_for_status()
        raw = response.json()
        if raw.get('s') == 'ok' and raw.get('t'):
            frame = pd.DataFrame({k: raw[v] for k,v in
                [('open','o'),('high','h'),('low','l'),('close','c'),('volume','v')]},
                index=pd.to_datetime(raw['t'], unit='s'))
            frame[['open','high','low','close']] *= 1000.0
            return finish(frame, 'VNDirect')
    except Exception as exc:
        errors.append(str(exc))
    try:
        frame = yf.Ticker(f'{symbol}.VN').history(
            start=(datetime.now()-timedelta(days=days)).strftime('%Y-%m-%d'), auto_adjust=False)
        frame = frame.rename(columns=str.lower)
        return finish(frame, 'Yahoo Finance')
    except Exception as exc:
        errors.append(str(exc))
    try:
        raw = json.loads(cache.read_text(encoding='utf-8'))
        if raw.get('ticker') == symbol:
            frame = pd.DataFrame(raw['rows']).set_index('date')
            return _normalize_prices(frame, symbol, days, raw['source'], cached=True)
    except (OSError, ValueError, KeyError, TypeError):
        pass
    raise DataUnavailableError(f'Không tải được giá của {symbol}. Kiểm tra mã, kết nối hoặc thử lại nguồn dữ liệu; không tạo giá mô phỏng.')


def _yahoo_fundamentals(symbol):
    stock = yf.Ticker(f'{symbol}.VN')
    info = stock.info or {}
    if not info.get('regularMarketPrice') and not info.get('currentPrice'):
        return {}
    result = {'ticker': symbol, 'name': info.get('longName') or info.get('shortName') or symbol,
              'sector': info.get('industry') or info.get('sector') or 'Chưa xác định',
              'exchange': info.get('exchange') or 'Chưa xác định',
              'description': info.get('longBusinessSummary') or '',
              'shares_outstanding': info.get('sharesOutstanding') or 0,
              'financial_history': [], 'data_source': 'Yahoo Finance',
              'last_updated': datetime.now().isoformat(timespec='seconds')}
    result['sector_code'] = infer_sector_code(info)
    result['dividend_yield'] = (info.get('dividendYield') or 0) * 100
    fin, balance, cashflow = stock.financials, stock.balance_sheet, stock.cashflow
    fields = {'revenue': (fin, 'Total Revenue'), 'gross_profit': (fin, 'Gross Profit'),
              'ebit': (fin, 'Operating Income'), 'net_income': (fin, 'Net Income'),
              'total_assets': (balance, 'Total Assets'), 'equity': (balance, 'Stockholders Equity'),
              'debt': (balance, 'Total Debt'), 'cash': (balance, 'Cash And Cash Equivalents'),
              'ocf': (cashflow, 'Operating Cash Flow'), 'capex': (cashflow, 'Capital Expenditure')}
    if fin is not None and not fin.empty:
        for column in sorted(fin.columns)[-4:]:
            row = {'year': str(column.year)}
            for field, (frame, label) in fields.items():
                if frame is not None and label in frame.index and column in frame.columns:
                    value = float(frame.loc[label, column])
                    if np.isfinite(value):
                        row[field] = (abs(value) if field == 'capex' else value) / 1e9
            if 'ocf' in row and 'capex' in row:
                row['fcf'] = row['ocf'] - row['capex']
            result['financial_history'].append(row)
    return result


def fetch_stock_fundamentals(ticker: str) -> Dict[str, Any]:
    symbol = clean_ticker(ticker)
    cache = CACHE_DIR / f'{symbol}_financials_v2.json'
    partial = {}
    for provider in [vci.fundamentals, _yahoo_fundamentals]:
        try:
            result = provider(symbol)
            if result and result.get('ticker') == symbol:
                if not partial:
                    partial = result
                required = {'revenue', 'net_income', 'total_assets', 'equity'}
                if len(result.get('financial_history', [])) >= 2 and all(
                        required <= row.keys() for row in result['financial_history'][-2:]):
                    _write(cache, result)
                    return result
        except Exception:
            continue
    try:
        cached = json.loads(cache.read_text(encoding='utf-8'))
        if cached.get('ticker') == symbol and cached.get('data_source') in ['Vietcap', 'Yahoo Finance']:
            cached['cached'] = True
            cached['data_warning'] = 'BCTC từ cache; thời điểm tải: ' + cached.get('last_updated', 'chưa rõ')
            return cached
    except (OSError, ValueError):
        pass
    return partial or {'ticker': symbol, 'name': symbol, 'sector': 'Chưa xác định',
                       'sector_code': 'GENERAL', 'exchange': 'Chưa xác định',
                       'description': '', 'shares_outstanding': 0, 'financial_history': [],
                       'data_source': 'Không có BCTC', 'data_warning': 'Chưa có BCTC của mã này.'}


def get_preset_fundamentals(sym: str) -> Dict[str, Any]:
    """
    Dữ liệu mẫu cố định dành riêng cho kiểm thử; không xác nhận là BCTC kiểm toán.
    Luồng phân tích thực không gọi hàm này.
    """
    presets = {
        "HPG": {
            "current_price": 20100.0,
            "pe": 7.35,
            "forward_pe": 6.80,
            "pb": 1.20,
            "market_cap_bil": 146328.0,
            "beta": 1.25,
            "dividend_yield": 0.0,
            "roe": 17.72,
            "roa": 8.45,
            "gross_margin": 13.80,
            "net_margin": 8.95,
            "rev_growth_yoy": 53.60,
            "earnings_growth_yoy": 42.10,
            "debt_to_equity": 0.65,
            "current_ratio": 1.45,
            "quick_ratio": 0.88,
            "shares_outstanding": 7_280_000_000,
            "financial_history": [
                {"year": "2022", "revenue": 141409.0, "gross_profit": 16677.0, "ebit": 10550.0, "net_income": 8444.0, "total_assets": 170336.0, "equity": 96113.0, "debt": 57888.0, "cash": 34600.0, "ocf": 12400.0, "capex": 24000.0, "fcf": -11600.0},
                {"year": "2023", "revenue": 120355.0, "gross_profit": 13175.0, "ebit": 8920.0, "net_income": 6800.0, "total_assets": 187783.0, "equity": 102555.0, "debt": 65355.0, "cash": 34100.0, "ocf": 14200.0, "capex": 22500.0, "fcf": -8300.0},
                {"year": "2024", "revenue": 140550.0, "gross_profit": 19400.0, "ebit": 15800.0, "net_income": 12100.0, "total_assets": 210500.0, "equity": 115200.0, "debt": 71200.0, "cash": 32800.0, "ocf": 18500.0, "capex": 26000.0, "fcf": -7500.0},
                {"year": "2025", "revenue": 168200.0, "gross_profit": 24200.0, "ebit": 20500.0, "net_income": 16500.0, "total_assets": 235000.0, "equity": 129000.0, "debt": 74500.0, "cash": 36000.0, "ocf": 24800.0, "capex": 19000.0, "fcf": 5800.0}
            ]
        },
        "FPT": {
            "current_price": 58200.0,
            "pe": 12.38,
            "forward_pe": 11.20,
            "pb": 2.74,
            "market_cap_bil": 84972.0,
            "beta": 0.85,
            "dividend_yield": 2.10,
            "roe": 27.06,
            "roa": 13.80,
            "gross_margin": 39.50,
            "net_margin": 15.20,
            "rev_growth_yoy": 19.50,
            "earnings_growth_yoy": 21.40,
            "debt_to_equity": 0.42,
            "current_ratio": 1.62,
            "quick_ratio": 1.45,
            "shares_outstanding": 1_460_000_000,
            "financial_history": [
                {"year": "2022", "revenue": 44010.0, "gross_profit": 17200.0, "ebit": 7650.0, "net_income": 5310.0, "total_assets": 51654.0, "equity": 25345.0, "debt": 12450.0, "cash": 19500.0, "ocf": 6800.0, "capex": 3800.0, "fcf": 3000.0},
                {"year": "2023", "revenue": 52618.0, "gross_profit": 20600.0, "ebit": 9200.0, "net_income": 6465.0, "total_assets": 60280.0, "equity": 29800.0, "debt": 14100.0, "cash": 24400.0, "ocf": 8200.0, "capex": 4500.0, "fcf": 3700.0},
                {"year": "2024", "revenue": 62850.0, "gross_profit": 24800.0, "ebit": 11100.0, "net_income": 7850.0, "total_assets": 71500.0, "equity": 35600.0, "debt": 15800.0, "cash": 28500.0, "ocf": 10100.0, "capex": 5200.0, "fcf": 4900.0},
                {"year": "2025", "revenue": 74500.0, "gross_profit": 29500.0, "ebit": 13400.0, "net_income": 9520.0, "total_assets": 84200.0, "equity": 42500.0, "debt": 17200.0, "cash": 33200.0, "ocf": 12400.0, "capex": 5900.0, "fcf": 6500.0}
            ]
        },
        "VCB": {
            "current_price": 56300.0,
            "pe": 11.42,
            "forward_pe": 10.10,
            "pb": 1.89,
            "market_cap_bil": 314660.0,
            "beta": 0.78,
            "dividend_yield": 1.80,
            "roe": 18.03,
            "roa": 1.95,
            "gross_margin": 62.00,
            "net_margin": 42.50,
            "rev_growth_yoy": 15.20,
            "earnings_growth_yoy": 12.80,
            "debt_to_equity": 8.20,
            "current_ratio": 1.15,
            "quick_ratio": 1.15,
            "shares_outstanding": 5_589_000_000,
            "financial_history": [
                {"year": "2022", "revenue": 68050.0, "gross_profit": 42500.0, "ebit": 37360.0, "net_income": 29899.0, "total_assets": 1814000.0, "equity": 136000.0, "debt": 1650000.0, "cash": 280000.0, "ocf": 35000.0, "capex": 3500.0, "fcf": 31500.0},
                {"year": "2023", "revenue": 72500.0, "gross_profit": 46200.0, "ebit": 41240.0, "net_income": 33010.0, "total_assets": 1839000.0, "equity": 162000.0, "debt": 1655000.0, "cash": 310000.0, "ocf": 38000.0, "capex": 4000.0, "fcf": 34000.0},
                {"year": "2024", "revenue": 79800.0, "gross_profit": 51500.0, "ebit": 45800.0, "net_income": 36600.0, "total_assets": 1980000.0, "equity": 188000.0, "debt": 1765000.0, "cash": 345000.0, "ocf": 42500.0, "capex": 4500.0, "fcf": 38000.0},
                {"year": "2025", "revenue": 89500.0, "gross_profit": 58200.0, "ebit": 51900.0, "net_income": 41500.0, "total_assets": 2180000.0, "equity": 218000.0, "debt": 1930000.0, "cash": 390000.0, "ocf": 48000.0, "capex": 5000.0, "fcf": 43000.0}
            ]
        },
        "MWG": {
            "current_price": 75600.0,
            "pe": 11.14,
            "forward_pe": 10.20,
            "pb": 3.11,
            "market_cap_bil": 110527.0,
            "beta": 1.15,
            "dividend_yield": 1.20,
            "roe": 30.07,
            "roa": 9.80,
            "gross_margin": 23.50,
            "net_margin": 4.10,
            "rev_growth_yoy": 29.60,
            "earnings_growth_yoy": 85.00,
            "debt_to_equity": 0.85,
            "current_ratio": 1.35,
            "quick_ratio": 0.55,
            "shares_outstanding": 1_462_000_000,
            "financial_history": [
                {"year": "2022", "revenue": 133405.0, "gross_profit": 30500.0, "ebit": 6100.0, "net_income": 4102.0, "total_assets": 55834.0, "equity": 23924.0, "debt": 22400.0, "cash": 15200.0, "ocf": 5100.0, "capex": 4200.0, "fcf": 900.0},
                {"year": "2023", "revenue": 118280.0, "gross_profit": 22400.0, "ebit": 850.0, "net_income": 168.0, "total_assets": 60110.0, "equity": 23300.0, "debt": 24200.0, "cash": 24300.0, "ocf": 8500.0, "capex": 2100.0, "fcf": 6400.0},
                {"year": "2024", "revenue": 134200.0, "gross_profit": 28800.0, "ebit": 5200.0, "net_income": 3850.0, "total_assets": 66500.0, "equity": 27200.0, "debt": 23500.0, "cash": 28000.0, "ocf": 11200.0, "capex": 2800.0, "fcf": 8400.0},
                {"year": "2025", "revenue": 156000.0, "gross_profit": 34500.0, "ebit": 7400.0, "net_income": 5600.0, "total_assets": 73200.0, "equity": 32100.0, "debt": 22800.0, "cash": 31500.0, "ocf": 13500.0, "capex": 3200.0, "fcf": 10300.0}
            ]
        },
        "SSI": {
            "current_price": 19000.0,
            "pe": 10.92,
            "forward_pe": 9.80,
            "pb": 1.40,
            "market_cap_bil": 37316.0,
            "beta": 1.45,
            "dividend_yield": 3.00,
            "roe": 13.86,
            "roa": 5.10,
            "gross_margin": 45.00,
            "net_margin": 32.50,
            "rev_growth_yoy": 6.00,
            "earnings_growth_yoy": 18.20,
            "debt_to_equity": 1.95,
            "current_ratio": 1.42,
            "quick_ratio": 1.42,
            "shares_outstanding": 1_964_000_000,
            "financial_history": [
                {"year": "2022", "revenue": 6517.0, "gross_profit": 3100.0, "ebit": 2110.0, "net_income": 1698.0, "total_assets": 52226.0, "equity": 22340.0, "debt": 27800.0, "cash": 14200.0, "ocf": 3200.0, "capex": 350.0, "fcf": 2850.0},
                {"year": "2023", "revenue": 7285.0, "gross_profit": 3650.0, "ebit": 2840.0, "net_income": 2173.0, "total_assets": 68500.0, "equity": 22700.0, "debt": 43500.0, "cash": 18500.0, "ocf": 4100.0, "capex": 420.0, "fcf": 3680.0},
                {"year": "2024", "revenue": 8650.0, "gross_profit": 4450.0, "ebit": 3550.0, "net_income": 2780.0, "total_assets": 76500.0, "equity": 26500.0, "debt": 47500.0, "cash": 22000.0, "ocf": 4900.0, "capex": 480.0, "fcf": 4420.0},
                {"year": "2025", "revenue": 10200.0, "gross_profit": 5400.0, "ebit": 4350.0, "net_income": 3450.0, "total_assets": 85000.0, "equity": 30800.0, "debt": 51200.0, "cash": 25500.0, "ocf": 5800.0, "capex": 550.0, "fcf": 5250.0}
            ]
        },
        "VHM": {
            "current_price": 43500.0,
            "pe": 6.80,
            "forward_pe": 6.20,
            "pb": 0.98,
            "market_cap_bil": 189400.0,
            "beta": 1.10,
            "dividend_yield": 2.50,
            "roe": 18.50,
            "roa": 7.20,
            "gross_margin": 36.50,
            "net_margin": 24.00,
            "rev_growth_yoy": 12.00,
            "earnings_growth_yoy": 10.50,
            "debt_to_equity": 0.55,
            "current_ratio": 1.48,
            "quick_ratio": 0.72,
            "shares_outstanding": 4_354_000_000,
            "financial_history": [
                {"year": "2022", "revenue": 62392.0, "gross_profit": 31200.0, "ebit": 38500.0, "net_income": 29000.0, "total_assets": 361882.0, "equity": 148400.0, "debt": 66200.0, "cash": 12500.0, "ocf": 18200.0, "capex": 8500.0, "fcf": 9700.0},
                {"year": "2023", "revenue": 103334.0, "gross_profit": 35200.0, "ebit": 43200.0, "net_income": 33371.0, "total_assets": 447360.0, "equity": 182600.0, "debt": 71500.0, "cash": 15400.0, "ocf": 22400.0, "capex": 9200.0, "fcf": 13200.0},
                {"year": "2024", "revenue": 115000.0, "gross_profit": 39500.0, "ebit": 47500.0, "net_income": 36200.0, "total_assets": 495000.0, "equity": 215000.0, "debt": 78000.0, "cash": 18200.0, "ocf": 26500.0, "capex": 10500.0, "fcf": 16000.0},
                {"year": "2025", "revenue": 128000.0, "gross_profit": 44200.0, "ebit": 52800.0, "net_income": 40500.0, "total_assets": 540000.0, "equity": 248000.0, "debt": 82000.0, "cash": 21500.0, "ocf": 31000.0, "capex": 11800.0, "fcf": 19200.0}
            ]
        }
    }
    return presets.get(clean_ticker(sym), {})


def sync_market_price(fundamentals, prices):
    """Use the chart's last close consistently across valuation and recommendations."""
    fundamentals['current_price'] = float(prices['close'].iloc[-1])
    fundamentals['price_as_of'] = prices.attrs.get('price_as_of')
    fundamentals.setdefault('dividend_yield', 0.0)
    rows = fundamentals.get('financial_history', [])
    shares = fundamentals.get('shares_outstanding', 0)
    if rows and shares > 0:
        ni, equity = rows[-1].get('net_income', 0), rows[-1].get('equity', 0)
        fundamentals['pe'] = fundamentals['current_price'] * shares / (ni*1e9) if ni > 0 else 0.0
        fundamentals['pb'] = fundamentals['current_price'] * shares / (equity*1e9) if equity > 0 else 0.0
    return fundamentals
