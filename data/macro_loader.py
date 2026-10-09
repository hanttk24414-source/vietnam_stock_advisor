"""
Module thu thập và chuẩn hóa dữ liệu vĩ mô Việt Nam.
Nguồn dữ liệu:
1. VNDirect dchart API: Điểm số lịch sử VN-Index và thanh khoản hàng ngày.
2. Yahoo Finance: Tỷ giá USD/VND (USDVND=X), Dầu thô (CL=F), Vàng thế giới (GC=F).
3. Tổng cục Thống kê (GSO) & Ngân hàng Nhà nước (SBV): GDP, CPI, Lãi suất, Tín dụng, Cung tiền M2.
"""

import json
import os
import time
from datetime import datetime, timedelta
import pandas as pd
import requests
import yfinance as yf
from config import CACHE_DIR, MACRO_DEFAULTS

MACRO_CACHE_FILE = CACHE_DIR / "macro_data.json"

def _demo_mode():
    return os.getenv('STOCK_ADVISOR_DEMO', '').strip().lower() in {'1', 'true', 'yes'}


DEFAULT_MACRO_FACTS = {
    "gdp_growth_2024": 6.82,
    "gdp_growth_2025": 6.95,
    "gdp_growth_latest_quarter": 7.40,
    "gdp_target_year": 7.00,
    "cpi_yoy": 3.45,
    "cpi_core_yoy": 2.70,
    "cpi_target": 4.00,
    "refinancing_rate": 4.50,
    "discount_rate": 3.00,
    "interbank_overnight_rate": 3.85,
    "interbank_1m_rate": 4.25,
    "credit_growth_ytd": 14.2,
    "m2_growth_ytd": 11.5,
    "fdi_disbursed_usd_bn": 24.8,
    "trade_surplus_usd_bn": 22.4,
    "gov_bond_10y_yield": 3.20,
    "last_updated": "2026-10-09"
}

def fetch_vnindex_history(days: int = 365) -> pd.DataFrame:
    """
    Tải lịch sử điểm số và khối lượng giao dịch của chỉ số VN-Index
    từ VNDirect Chart API. Có cơ chế fallback tự động.
    """
    to_time = int(time.time())
    from_time = to_time - int(days * 86400 * 1.5) # lấy dư ngày giao dịch
    url = f"https://dchart-api.vndirect.com.vn/dchart/history?resolution=D&symbol=VNINDEX&from={from_time}&to={to_time}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("s") == "ok" and "t" in data and len(data["t"]) > 0:
                df = pd.DataFrame({
                    "date": [datetime.fromtimestamp(ts) for ts in data["t"]],
                    "open": data["o"],
                    "high": data["h"],
                    "low": data["l"],
                    "close": data["c"],
                    "volume": data["v"]
                })
                df.set_index("date", inplace=True)
                df.sort_index(inplace=True)
                df = df.tail(days)
                df.attrs['data_source'] = 'VNDirect dchart'
                return df
    except Exception as e:
        print(f"[Warning] Không thể lấy VNINDEX từ VNDirect API: {e}. Sử dụng dữ liệu dự phòng.")
        
    # Cache hiện tại chưa có bằng chứng nguồn, chỉ dùng để trình diễn.
    if _demo_mode() and MACRO_CACHE_FILE.exists():
        try:
            with open(MACRO_CACHE_FILE, "r", encoding="utf-8") as f:
                cached = json.load(f)
                if "vnindex_history" in cached:
                    df = pd.DataFrame(cached["vnindex_history"])
                    df["date"] = pd.to_datetime(df["date"])
                    df.set_index("date", inplace=True)
                    df = df.tail(days)
                    df.attrs['data_source'] = 'CACHE DEMO (chưa xác minh)'
                    return df
        except Exception:
            pass

    if not _demo_mode():
        raise RuntimeError('Không có dữ liệu VN-Index thật; ngừng phân tích, không tạo chỉ số ngẫu nhiên.')

    # Fallback giả lập chỉ trong chế độ demo
    dates = pd.date_range(end=datetime.now(), periods=days, freq="B")
    base_val = 1500.0
    import numpy as np
    np.random.seed(42)
    changes = np.random.normal(0.0005, 0.01, size=len(dates))
    prices = base_val * np.cumprod(1 + changes)
    df = pd.DataFrame({
        "open": prices * 0.998,
        "high": prices * 1.008,
        "low": prices * 0.992,
        "close": prices,
        "volume": np.random.randint(400_000_000, 750_000_000, size=len(dates))
    }, index=dates)
    df.attrs['data_source'] = 'DỮ LIỆU GIẢ LẬP (DEMO)'
    return df

def fetch_macro_indicators() -> dict:
    """
    Thu thập các chỉ số vĩ mô kết hợp:
    1. VNINDEX điểm số và biến động
    2. Tỷ giá USD/VND, Dầu, Vàng từ Yahoo Finance
    3. Các chỉ tiêu kinh tế vĩ mô chính thức của Việt Nam (GSO & SBV)
    """
    if not _demo_mode():
        raise RuntimeError(
            'Chưa cấu hình nguồn GDP/CPI/lãi suất/ERP có thể xác minh cho chế độ THẬT. '
            'Các giá trị vĩ mô gắn sẵn chỉ dùng trình diễn. '
            'Đặt STOCK_ADVISOR_DEMO=1 để chạy bản mẫu, hoặc bổ sung dữ liệu vĩ mô xác minh.'
        )
    result = dict(DEFAULT_MACRO_FACTS)
    result['data_mode'] = 'DEMO'
    result['data_source'] = 'THAM SỐ MẪU - CHƯA XÁC MINH, KHÔNG DÙNG ĐẦU TƯ'
    
    # 1. Lấy dữ liệu thị trường VN-Index
    try:
        vnindex_df = fetch_vnindex_history(days=250)
        if not vnindex_df.empty:
            latest_close = float(vnindex_df["close"].iloc[-1])
            prev_close = float(vnindex_df["close"].iloc[-2]) if len(vnindex_df) > 1 else latest_close
            chg_1d = (latest_close - prev_close) / prev_close * 100
            
            # Tính hiệu suất 1 tháng, 1 năm
            chg_1m = (latest_close / float(vnindex_df["close"].iloc[-22]) - 1) * 100 if len(vnindex_df) >= 22 else 0.0
            chg_1y = (latest_close / float(vnindex_df["close"].iloc[0]) - 1) * 100 if len(vnindex_df) > 0 else 0.0
            avg_vol_20d = float(vnindex_df["volume"].tail(20).mean())
            
            result["vnindex_current"] = round(latest_close, 2)
            result["vnindex_change_1d"] = round(chg_1d, 2)
            result["vnindex_change_1m"] = round(chg_1m, 2)
            result["vnindex_change_1y"] = round(chg_1y, 2)
            result["vnindex_avg_volume_20d"] = int(avg_vol_20d)
            result["vnindex_pe"] = 14.8  # P/E trung bình thị trường VN-Index
            result["vnindex_pb"] = 1.68  # P/B trung bình thị trường VN-Index
    except Exception as e:
        print(f"[Warning] Lỗi khi xử lý VN-Index: {e}")
        result["vnindex_current"] = 1738.99
        result["vnindex_change_1d"] = 0.0
        result["vnindex_pe"] = 14.8

    # 2. Lấy tỷ giá USD/VND và Hàng hóa từ Yahoo Finance
    try:
        usdvnd = yf.Ticker("USDVND=X").history(period="5d")
        if not usdvnd.empty:
            result["usd_vnd_rate"] = round(float(usdvnd["Close"].iloc[-1]), 0)
        else:
            result["usd_vnd_rate"] = 25889.0
    except Exception:
        result["usd_vnd_rate"] = 25889.0

    try:
        oil = yf.Ticker("CL=F").history(period="5d")
        if not oil.empty:
            result["crude_oil_usd"] = round(float(oil["Close"].iloc[-1]), 2)
        else:
            result["crude_oil_usd"] = 90.70
    except Exception:
        result["crude_oil_usd"] = 90.70

    try:
        gold = yf.Ticker("GC=F").history(period="5d")
        if not gold.empty:
            result["gold_usd_oz"] = round(float(gold["Close"].iloc[-1]), 2)
        else:
            result["gold_usd_oz"] = 4216.60
    except Exception:
        result["gold_usd_oz"] = 4216.60

    # 3. Tính toán Phần bù rủi ro vốn cổ phần (Equity Risk Premium - ERP)
    # Lợi suất Earning Yield thị trường = 1 / P/E
    pe = result.get("vnindex_pe", 14.8)
    market_earnings_yield = (1.0 / pe) * 100.0 if pe > 0 else 6.75
    bond_yield = result.get("gov_bond_10y_yield", 3.20)
    result["market_earnings_yield"] = round(market_earnings_yield, 2)
    result["equity_risk_premium"] = round(market_earnings_yield - bond_yield, 2)

    # Đánh giá môi trường vĩ mô định lượng
    # Nếu ERP > 3.0% và Lãi suất điều hành ổn định -> Môi trường đầu tư cổ phiếu hấp dẫn
    if result["equity_risk_premium"] >= 3.0:
        result["macro_stance"] = "TÍCH CỰC - MÔI TRƯỜNG ĐẦU TƯ THUẬN LỢI"
        result["macro_score"] = 82
    elif result["equity_risk_premium"] >= 1.5:
        result["macro_stance"] = "TRUNG LẬP - CƠ HỘI PHÂN HÓA THEO NGÀNH"
        result["macro_score"] = 68
    else:
        result["macro_stance"] = "THẬN TRỌNG - RỦI RO ĐỊNH GIÁ CAO"
        result["macro_score"] = 48

    # Lưu cache
    try:
        to_save = dict(result)
        # Bổ sung mẫu vnindex_history cho cache
        if "vnindex_df" in locals() and not vnindex_df.empty:
            df_reset = vnindex_df.tail(120).reset_index()
            df_reset["date"] = df_reset["date"].dt.strftime("%Y-%m-%d")
            to_save["vnindex_history"] = df_reset.to_dict(orient="records")
        with open(MACRO_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(to_save, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Warning] Lưu macro cache thất bại: {e}")

    return result
