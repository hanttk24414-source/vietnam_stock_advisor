"""DNSE OpenAPI: daily OHLCV for Vietnam-listed stocks and VN-Index.

Read credentials from local .env or environment. Never commit the .env file.
DNSE SDK: pip install dnse-sdk-openapi (import name: dnse).
"""
from __future__ import annotations
import json
import os
from datetime import datetime, timedelta, timezone
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

INDEX_SYMBOLS = {"VNINDEX", "VN30", "HNXINDEX", "UPCOMINDEX"}

def dnse_configured() -> bool:
    return bool(os.getenv("DNSE_API_KEY") and os.getenv("DNSE_API_SECRET"))

def fetch_dnse_history(symbol: str, days: int = 365) -> pd.DataFrame:
    if not dnse_configured():
        raise RuntimeError("Thiếu DNSE_API_KEY hoặc DNSE_API_SECRET trong .env")
    try:
        from dnse import DNSEClient
    except ImportError as exc:
        raise RuntimeError("Thiếu gói dnse-sdk-openapi; chạy pip install -r requirements.txt") from exc

    symbol = symbol.strip().upper().replace(".VN", "")
    if not symbol.isalnum() or not (2 <= len(symbol) <= 12):
        raise ValueError("Mã chứng khoán không hợp lệ")
    if days < 1:
        raise ValueError("days phải lớn hơn 0")

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=int(days * 1.65) + 14)
    client_args = {
        "api_key": os.environ["DNSE_API_KEY"],
        "api_secret": os.environ["DNSE_API_SECRET"],
    }
    if os.getenv("DNSE_BASE_URL"):
        client_args["base_url"] = os.environ["DNSE_BASE_URL"]
    client = DNSEClient(**client_args)
    market = "INDEX" if symbol in INDEX_SYMBOLS else "STOCK"
    status, raw_body = client.get_ohlc(market, query={
        "symbol": symbol, "resolution": "1D",
        "from": int(since.timestamp()), "to": int(now.timestamp()),
    })
    if int(status) != 200:
        raise RuntimeError(f"DNSE HTTP {status} cho {symbol}")
    payload = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
    keys = ("t", "o", "h", "l", "c", "v")
    if not isinstance(payload, dict) or any(not isinstance(payload.get(k), list) for k in keys):
        raise ValueError("Phản hồi DNSE thiếu trường OHLCV")
    count = len(payload["t"])
    if count == 0 or any(len(payload[k]) != count for k in keys):
        raise ValueError("DNSE không có dữ liệu hoặc mảng OHLCV không đồng bộ")

    times = pd.to_datetime(payload["t"], unit="s", utc=True)
    dates = times.tz_convert("Asia/Ho_Chi_Minh").tz_localize(None).normalize()
    df = pd.DataFrame({
        "open": payload["o"], "high": payload["h"], "low": payload["l"],
        "close": payload["c"], "volume": payload["v"]
    }, index=dates)
    df.index.name = "date"
    df = df.apply(pd.to_numeric, errors="coerce").dropna()
    if df.empty or (df["close"] <= 0).any() or (df["volume"] < 0).any():
        raise ValueError("Dữ liệu giá hoặc thanh khoản DNSE không hợp lệ")
    factor_override = os.getenv("DNSE_PRICE_MULTIPLIER")
    factor = float(factor_override) if factor_override else (
        1000.0 if market == "STOCK" and df["close"].median() < 1000 else 1.0
    )
    if not 0 < factor < 1000000:
        raise ValueError("DNSE_PRICE_MULTIPLIER không hợp lệ")
    for col in ("open", "high", "low", "close"):
        df[col] = df[col] * factor
    df = df.sort_index()
    df = df.loc[~df.index.duplicated(keep="last")].tail(days)
    df.attrs["data_source"] = "DNSE OpenAPI"
    return df
