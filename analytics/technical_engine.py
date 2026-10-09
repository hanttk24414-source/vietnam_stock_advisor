"""
Module phân tích kỹ thuật và định lượng rủi ro - lợi suất cổ phiếu.
Tính toán:
1. Đường xu hướng: SMA 20, SMA 50, SMA 200, EMA 20.
2. Động lượng & Dao động: RSI (14), MACD (12, 26, 9) & Histogram.
3. Độ biến động: Bollinger Bands (20, 2), Average True Range (ATR 14).
4. Thanh khoản: Khối lượng trung bình 20 phiên, Tỷ lệ đột biến khối lượng.
5. Định lượng rủi ro: Lợi suất quy năm, Biến động quy năm, Beta, Sharpe Ratio, Max Drawdown.
6. Tín hiệu kỹ thuật tổng hợp (Bullish / Neutral / Bearish).
"""

from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
from config import MACRO_DEFAULTS

def compute_technical_indicators(df: pd.DataFrame, vnindex_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Tính toán toàn bộ các chỉ báo kỹ thuật và thống kê rủi ro tài chính.
    """
    if df.empty or len(df) < 20:
        return {}

    close = df["close"].copy()
    high = df["high"].copy()
    low = df["low"].copy()
    volume = df["volume"].copy()
    
    current_price = float(close.iloc[-1])
    prev_close = float(close.iloc[-2]) if len(close) > 1 else current_price
    chg_1d = (current_price - prev_close) / prev_close * 100
    
    # Biến động các khung thời gian
    chg_1w = (current_price / float(close.iloc[-5]) - 1) * 100 if len(close) >= 5 else 0.0
    chg_1m = (current_price / float(close.iloc[-22]) - 1) * 100 if len(close) >= 22 else 0.0
    chg_1y = (current_price / float(close.iloc[0]) - 1) * 100 if len(close) >= 1 else 0.0
    
    high_52w = float(high.max())
    low_52w = float(low.min())
    pct_from_52w_high = (current_price / high_52w - 1) * 100
    pct_from_52w_low = (current_price / low_52w - 1) * 100

    # 1. Đường xu hướng MA
    sma20 = float(close.rolling(window=20).mean().iloc[-1]) if len(close) >= 20 else current_price
    sma50 = float(close.rolling(window=50).mean().iloc[-1]) if len(close) >= 50 else sma20
    sma200 = float(close.rolling(window=200).mean().iloc[-1]) if len(close) >= 200 else sma50
    ema20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1]) if len(close) >= 20 else current_price

    # 2. RSI (14)
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=14, min_periods=14).mean()
    avg_loss = loss.rolling(window=14, min_periods=14).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi_series = 100 - (100 / (1 + rs))
    rsi = float(rsi_series.dropna().iloc[-1]) if not rsi_series.dropna().empty else 50.0

    # 3. MACD (12, 26, 9)
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_hist = macd_line - signal_line
    
    cur_macd = float(macd_line.iloc[-1])
    cur_signal = float(signal_line.iloc[-1])
    cur_hist = float(macd_hist.iloc[-1])

    # 4. Bollinger Bands (20, 2)
    bb_rolling = close.rolling(window=20)
    bb_mid = bb_rolling.mean()
    bb_std = bb_rolling.std()
    bb_upper = bb_mid + (bb_std * 2)
    bb_lower = bb_mid - (bb_std * 2)
    
    cur_bb_upper = float(bb_upper.iloc[-1]) if not bb_upper.empty else current_price * 1.05
    cur_bb_mid = float(bb_mid.iloc[-1]) if not bb_mid.empty else current_price
    cur_bb_lower = float(bb_lower.iloc[-1]) if not bb_lower.empty else current_price * 0.95
    cur_bb_pct_b = (current_price - cur_bb_lower) / (cur_bb_upper - cur_bb_lower) if (cur_bb_upper - cur_bb_lower) > 0 else 0.5

    # 5. Average True Range (ATR 14)
    prev_close_series = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close_series).abs()
    tr3 = (low - prev_close_series).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr14 = float(tr.rolling(window=14).mean().iloc[-1]) if len(tr) >= 14 else float(tr.mean())

    # 6. Thanh khoản
    vol_sma20 = float(volume.rolling(window=20).mean().iloc[-1]) if len(volume) >= 20 else float(volume.mean())
    latest_vol = float(volume.iloc[-1])
    vol_surge_ratio = latest_vol / vol_sma20 if vol_sma20 > 0 else 1.0

    # 7. Thống kê Sinh lời và Rủi ro (Annualized Metrics)
    daily_returns = close.pct_change().dropna()
    ann_return = float(daily_returns.mean() * 252 * 100)
    ann_volatility = float(daily_returns.std() * np.sqrt(252) * 100) if len(daily_returns) > 5 else 25.0
    
    rf = MACRO_DEFAULTS["risk_free_rate"] * 100 # %
    sharpe_ratio = round((ann_return - rf) / ann_volatility, 2) if ann_volatility > 0 else 0.0

    # Maximum Drawdown (MDD)
    cumulative_returns = (1 + daily_returns).cumprod()
    peak = cumulative_returns.cummax()
    drawdown = (cumulative_returns - peak) / peak
    max_drawdown = float(drawdown.min() * 100)

    # Beta so với VN-Index
    beta = 1.0
    if vnindex_df is not None and not vnindex_df.empty:
        try:
            # Đồng bộ ngày giữa cổ phiếu và chỉ số
            common_idx = close.index.intersection(vnindex_df.index)
            if len(common_idx) > 30:
                stock_ret = close.loc[common_idx].pct_change().dropna()
                idx_ret = vnindex_df["close"].loc[common_idx].pct_change().dropna()
                aligned = pd.concat([stock_ret, idx_ret], axis=1).dropna()
                cov = np.cov(aligned.iloc[:, 0], aligned.iloc[:, 1])[0][1]
                idx_var = np.var(aligned.iloc[:, 1])
                if idx_var > 0:
                    beta = round(float(cov / idx_var), 2)
        except Exception:
            beta = 1.0

    # 8. Đánh giá Xu hướng Kỹ thuật Tổng hợp
    tech_score = 50
    reasons = []

    # Xu hướng MA
    if current_price > sma20 and sma20 > sma50:
        tech_score += 18
        reasons.append("Giá nằm trên MA20 và MA50 xác nhận xu hướng tăng ngắn-trung hạn mạnh mẽ.")
    elif current_price > sma20:
        tech_score += 10
        reasons.append("Giá nằm trên MA20 giữ vững kênh hỗ trợ ngắn hạn.")
    else:
        tech_score -= 10
        reasons.append("Giá giao dịch dưới MA20 phản ánh áp lực điều chỉnh ngắn hạn.")

    if current_price > sma200:
        tech_score += 12
        reasons.append("Giá duy trì trên MA200 bảo toàn cấu trúc tăng giá dài hạn.")
    else:
        tech_score -= 10
        reasons.append("Giá nằm dưới MA200 cho thấy xu hướng dài hạn đang chịu thử thách.")

    # Động lượng RSI
    if 45 <= rsi <= 65:
        tech_score += 10
        reasons.append(f"RSI ở mức {rsi:.1f} điểm trong vùng xung lực tăng lành mạnh, không quá mua.")
    elif rsi < 35:
        tech_score += 8
        reasons.append(f"RSI ở mức {rsi:.1f} điểm chạm vùng quá bán (Oversold), kỳ vọng xuất hiện nhịp hồi kỹ thuật.")
    elif rsi > 70:
        tech_score -= 5
        reasons.append(f"RSI ở mức {rsi:.1f} điểm tiến vào vùng quá mua (Overbought), rủi ro rung lắc ngắn hạn.")

    # MACD
    if cur_macd > cur_signal and cur_hist > 0:
        tech_score += 10
        reasons.append("Chỉ báo MACD cắt lên trên đường Signal và Histogram dương xác nhận đà tăng.")
    elif cur_macd > cur_signal:
        tech_score += 5
        reasons.append("MACD duy trì trên Signal line nhưng xung lực đang chậm lại.")
    else:
        tech_score -= 8
        reasons.append("MACD nằm dưới Signal line cảnh báo đà giảm tiếp diễn.")

    # Thanh khoản
    if vol_surge_ratio >= 1.2:
        tech_score += 10
        reasons.append(f"Khối lượng giao dịch tăng gấp {vol_surge_ratio:.2f} lần so với trung bình 20 phiên, dòng tiền nhập cuộc tích cực.")

    tech_score = max(10, min(100, tech_score))

    if tech_score >= 70:
        signal = "TÍCH CỰC (BULLISH)"
    elif tech_score >= 45:
        signal = "TRUNG LẬP / TÍCH LŨY (NEUTRAL)"
    else:
        signal = "TIÊU CỰC (BEARISH)"

    support_1 = round(min(sma20, cur_bb_lower), 0)
    support_2 = round(sma50, 0)
    resist_1 = round(max(cur_bb_upper, sma20 * 1.05), 0)
    resist_2 = round(high_52w, 0)

    return {
        "current_price": current_price,
        "change_1d_pct": round(chg_1d, 2),
        "change_1w_pct": round(chg_1w, 2),
        "change_1m_pct": round(chg_1m, 2),
        "change_1y_pct": round(chg_1y, 2),
        "high_52w": high_52w,
        "low_52w": low_52w,
        "pct_from_52w_high": round(pct_from_52w_high, 2),
        "pct_from_52w_low": round(pct_from_52w_low, 2),
        "sma20": round(sma20, 1),
        "sma50": round(sma50, 1),
        "sma200": round(sma200, 1),
        "ema20": round(ema20, 1),
        "rsi": round(rsi, 2),
        "macd": round(cur_macd, 2),
        "macd_signal": round(cur_signal, 2),
        "macd_hist": round(cur_hist, 2),
        "bb_upper": round(cur_bb_upper, 1),
        "bb_middle": round(cur_bb_mid, 1),
        "bb_lower": round(cur_bb_lower, 1),
        "bb_pct_b": round(cur_bb_pct_b, 3),
        "atr14": round(atr14, 1),
        "volume_latest": int(latest_vol),
        "volume_sma20": int(vol_sma20),
        "vol_surge_ratio": round(vol_surge_ratio, 2),
        "annualized_return_pct": round(ann_return, 2),
        "annualized_volatility_pct": round(ann_volatility, 2),
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown_pct": round(max_drawdown, 2),
        "beta": beta,
        "tech_score": tech_score,
        "overall_signal": signal,
        "support_levels": [support_1, support_2],
        "resistance_levels": [resist_1, resist_2],
        "reasons": reasons
    }
