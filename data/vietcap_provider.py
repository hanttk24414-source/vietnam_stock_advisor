"""Public Vietcap endpoints; normalize only explicitly identified financial fields.

Endpoint contract checked against thinh-vu/vnstock/explorer/vci (2026-10-09).
Amounts in financial statements are VND; internal annual amounts are billion VND.
"""
import math
import re
import unicodedata
from datetime import datetime, timedelta

import pandas as pd
import requests

TRADING = 'https://trading.vietcap.com.vn/api'
IQ = 'https://iq.vietcap.com.vn/api/iq-insight-service/v1'
HEADERS = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
           'Origin': 'https://trading.vietcap.com.vn',
           'Referer': 'https://trading.vietcap.com.vn/'}


def _get(url, **kwargs):
    response = requests.get(url, headers=HEADERS, timeout=10, **kwargs)
    response.raise_for_status()
    return response.json()


def listings():
    raw = _get(f'{TRADING}/price/symbols/getAll')
    rows = raw.get('data', []) if isinstance(raw, dict) else raw
    return {r['symbol']: {'name': r.get('organName') or r['symbol'],
                         'exchange': r.get('board', 'Chưa xác định')}
            for r in rows if r.get('type') == 'STOCK' and r.get('symbol')}


def history(symbol, days):
    response = requests.post(f'{TRADING}/chart/OHLCChart/gap-chart',
        headers=HEADERS, timeout=10,
        json={'timeFrame': 'ONE_DAY', 'symbols': [symbol],
              'to': int(datetime.now().timestamp()), 'countBack': days})
    response.raise_for_status()
    raw = response.json()
    rows = raw.get('data', []) if isinstance(raw, dict) else raw
    if not rows:
        return pd.DataFrame()
    r = rows[0]
    if r.get('symbol') and r['symbol'] != symbol:
        raise ValueError('Vietcap trả dữ liệu của mã khác')
    if not r.get('t'):
        return pd.DataFrame()
    # Chart endpoint quotes prices in VND (no price-dependent unit heuristic).
    df = pd.DataFrame({key: r[short] for key, short in
        [('open', 'o'), ('high', 'h'), ('low', 'l'), ('close', 'c'), ('volume', 'v')]},
        index=pd.to_datetime(r['t'], unit='s', utc=True).tz_convert('Asia/Ho_Chi_Minh').tz_localize(None).normalize())
    df.index.name = 'date'
    return df.loc[df.index >= pd.Timestamp(datetime.now().date() - timedelta(days=days))]


def _norm(value):
    value = unicodedata.normalize('NFKD', str(value).replace('đ', 'd').replace('Đ', 'D')).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]', '', value.replace('đ', 'd'))


# Exact aliases only: never guess an accounting line from a substring or row position.
ALIASES = {
    'revenue': ['Net sales', 'Revenue', 'Net revenue', 'Doanh thu thuần', 'Doanh thu thuần về bán hàng và cung cấp dịch vụ', 'Total operating income', 'Tổng thu nhập hoạt động'],
    'gross_profit': ['Gross profit', 'Lợi nhuận gộp về bán hàng và cung cấp dịch vụ', 'Lợi nhuận gộp'],
    'ebit': ['Operating profit', 'Operating income', 'Lợi nhuận thuần từ hoạt động kinh doanh'],
    'net_income': ['Net profit attributable to parent company', 'Net profit after tax attributable to parent company shareholders', 'Lợi nhuận sau thuế của cổ đông Công ty mẹ', 'Profit after tax for shareholders of the parent company', 'Net profit', 'Net income', 'Profit after tax', 'Lợi nhuận sau thuế thu nhập doanh nghiệp'],
    'total_assets': ['Total assets', 'Tổng cộng tài sản', 'Tổng tài sản'],
    'equity': ["Owners equity", "Owner's equity", 'Equity', 'Total equity', 'Vốn chủ sở hữu'],
    'cash': ['Cash and cash equivalents', 'Tiền và các khoản tương đương tiền'],
    'debt': ['Total debt', 'Interest bearing debt', 'Nợ vay'],
    'short_term_debt': ['Short term borrowings', 'Short term loans', 'Short-term borrowings and financial leases', 'Vay và nợ thuê tài chính ngắn hạn'],
    'long_term_debt': ['Long term borrowings', 'Long term loans', 'Long-term borrowings and financial leases', 'Vay và nợ thuê tài chính dài hạn'],
    'ocf': ['Net cash flows from operating activities', 'Net cash from operating activities', 'Cash flows from operating activities', 'Lưu chuyển tiền thuần từ hoạt động kinh doanh'],
    'capex': ['Purchase and construction of fixed assets and other long-term assets', 'Purchases of fixed assets and other long term assets', 'Purchase of fixed assets', 'Purchases of fixed assets', 'Purchase of property plant and equipment', 'Tiền chi để mua sắm xây dựng TSCĐ và các tài sản dài hạn khác'],
}


def _number(value):
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def normalize_statements(metadata, sections):
    """Join income/balance/cash statements by year, retain missing fields as absent."""
    metrics = [m for group in metadata.values() if isinstance(group, list) for m in group]
    titles = {m['field']: [_norm(m.get('titleEn', '')), _norm(m.get('titleVi', ''))]
              for m in metrics if m.get('field')}
    mapped = {}
    for target, aliases in ALIASES.items():
        # Alias order prefers attributable profit over consolidated profit.
        for alias in aliases:
            matches = [field for field, names in titles.items() if _norm(alias) in names]
            if len(matches) == 1:
                mapped[target] = matches[0]
                break
    by_year = {}
    for section in sections:
        for row in section.get('years', []):
            year = row.get('yearReport', row.get('year'))
            if year is None:
                continue
            record = by_year.setdefault(str(int(year)), {'year': str(int(year))})
            for target, field in mapped.items():
                value = _number(row.get(field))
                if value is not None:
                    record[target] = round(abs(value) / 1e9 if target == 'capex' else value / 1e9, 3)
    for row in by_year.values():
        if 'debt' not in row and 'short_term_debt' in row and 'long_term_debt' in row:
            row['debt'] = row['short_term_debt'] + row['long_term_debt']
        if 'ocf' in row and 'capex' in row:
            row['fcf'] = row['ocf'] - row['capex']
    return [by_year[y] for y in sorted(by_year)[-4:]]


def sector_code(name):
    name = _norm(name)
    for code, words in [('BANKING', ['nganhang', 'bank']),
                        ('BROKERAGE', ['chungkhoan', 'securities']),
                        ('TECH', ['congnghe', 'software', 'technology']),
                        ('STEEL', ['thep', 'steel']),
                        ('RETAIL', ['banle', 'retail']),
                        ('REAL_ESTATE', ['batdongsan', 'realestate'])]:
        if any(word in name for word in words):
            return code
    return 'GENERAL'


def fundamentals(symbol):
    details = _get(f'{IQ}/company/details', params={'ticker': symbol}).get('data') or {}
    if not isinstance(details, dict) or not details:
        return {}
    returned = details.get('ticker')
    if returned and returned != symbol:
        raise ValueError('Vietcap trả thông tin của mã khác')
    result = {'ticker': symbol, 'name': details.get('viOrganName') or details.get('enOrganName') or symbol,
              'sector': details.get('sectorVn') or details.get('sector') or 'Chưa xác định',
              'exchange': details.get('exchange') or details.get('board') or 'Chưa xác định',
              'description': re.sub('<[^>]+>', '', details.get('profile') or ''),
              'shares_outstanding': _number(details.get('numberOfSharesMktCap')) or 0,
              'financial_history': [], 'data_source': 'Vietcap',
              'last_updated': datetime.now().isoformat(timespec='seconds')}
    result['sector_code'] = sector_code(result['sector'])
    try:
        metadata = _get(f'{IQ}/company/{symbol}/financial-statement/metrics').get('data') or {}
        sections = [_get(f'{IQ}/company/{symbol}/financial-statement', params={'section': s}).get('data') or {}
                    for s in ['INCOME_STATEMENT', 'BALANCE_SHEET', 'CASH_FLOW']]
        result['financial_history'] = normalize_statements(metadata, sections)
    except (requests.RequestException, ValueError, TypeError, KeyError):
        result['data_warning'] = 'Không tải hoặc chuẩn hóa được đầy đủ BCTC Vietcap.'
    return result
