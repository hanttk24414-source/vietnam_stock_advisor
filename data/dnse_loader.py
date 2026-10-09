"""Optional DNSE OpenAPI OHLCV adapter.

Required environment: DNSE_API_KEY, DNSE_API_SECRET.
Optional: DNSE_BASE_URL, DNSE_PRICE_MULTIPLIER.
Install separately: python -m pip install dnse-sdk-openapi
No secrets are embedded in this repository.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone

import pandas as pd


def configured() -> bool:
    return bool(os.getenv("DNSE_API_KEY") and os.getenv("DNSE_API_SECRET"))


def fetch_daily_ohlcv(symbol: str, days: int) -> pd.DataFrame:
    """Return a date-indexed VND OHLCV DataFrame; raise on API/quality failures."""
    if not configured():
        raise RuntimeError("DNSE_API_KEY / DNSE_API_SECRET chưa được cấu hình")
    try:
        from dnse import DNSEClient
    except ImportError as exc:
        raise RuntimeError("Thiếu SDK DNSE: python -m pip install dnse-sdk-openapi") from exc

    symbol = symbol.strip().upper()
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=max(int(days * 1.6), 30) + 10)
    client = DNSEClient(
        api_key=os.environ["DNSE_API_KEY"],
        api_secret=os.environ["DNSE_API_SECRET"],
        base_url=os.getenv("DNSE_BASE_URL", "https://openapi.dnse.com.vn"),
    )
    bar_type = "INDEX" if symbol in {"VNINDEX", "VN30", "HNXINDEX", "UPCOMINDEX"} else "STOCK"
    status, body = client.get_ohlc(bar_type, query={
        "symbol": symbol,
        "resolution": "1D",
        "from": int(start.timestamp()),
        "to": int(now.timestamp()),
    })
    if int(status or 0) != 200:
        raise RuntimeError(f"DNSE từ chối yêu cầu {symbol}: HTTP {status}")
    payload = json.loads(body) if isinstance(body, str) else body
    fields = ("t", "o", "h", "l", "c", "v")
    if not isinstance(payload, dict) or any(not isinstance(payload.get(k), list) for k in fields):
        raise ValueError("DNSE thiếu dữ liệu OHLCV")
    count = len(payload["t"])
    if not count or any(len(payload[k]) != count for k in fields):
        raise ValueError("DNSE trả các mảng OHLCV rỗng hoặc không đồng bộ")

    index = pd.to_datetime(payload["t"], unit="s", utc=True)
    index = index.tz_convert("Asia/Ho_Chi_Minh").tz_localize(None).normalize()
    df = pd.DataFrame({
        "open": payload["o"],
        "high": payload["h"],
        "low": payload["l"],
        "close": payload["c"],
        "volume": payload["v"],
    }, index=index)
    df.index.name = "date"
    df = df.apply(pd.to_numeric, errors="coerce").dropna()
    if df.empty or (df["close"] <= 0).any() or (df["volume"] < 0).any():
        raise ValueError("DNSE OHLCV chứa giá hoặc khối lượng không hợp lệ")

    # DNSE stock quotes can be in 1,000 VND. A documented override avoids
    # silently changing units if a provider changes its response format.
    factor_env = os.getenv("DNSE_PRICE_MULTIPLIER")
    factor = float(factor_env) if factor_env else (
        1000.0 if bar_type == "STOCK" and float(df["close"].median()) < 1000 else 1.0
    )
    if factor <= 0:
        raise ValueError("DNSE_PRICE_MULTIPLIER phải lớn hơn 0")
    for col in ("open", "high", "low", "close"):
        df[col] *= factor
    df = df[~df.index.duplicated(keep="last")].sort_index().tail(days)
    df.attrs["data_source"] = "DNSE OpenAPI"
    return df
