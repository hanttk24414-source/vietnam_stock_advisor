"""
Module tự động tạo biểu đồ phân tích kỹ thuật, tài chính, radar scorecard
và kịch bản định giá phục vụ xuất báo cáo PDF và hiển thị giao diện.
"""

from pathlib import Path
from typing import Dict, Any, List
import matplotlib
matplotlib.use("Agg") # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Thiết lập font Arial cho Matplotlib trên Windows để hiển thị tiếng Việt không bị lỗi
plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans", "Calibri", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

PRIMARY_COLOR = "#1A365D"   # Deep Navy
SECONDARY_COLOR = "#2B6CB0" # Slate Blue
ACCENT_GREEN = "#2E7D32"    # Green
ACCENT_RED = "#C53030"      # Red
NEUTRAL_GREY = "#718096"
GRID_COLOR = "#E2E8F0"

def generate_technical_chart(price_df: pd.DataFrame, ticker: str, output_path: Path) -> str:
    """
    Vẽ biểu đồ giá lịch sử kèm đường trung bình MA20, MA50, MA200 và khối lượng giao dịch.
    """
    df = price_df.tail(120).copy()
    if df.empty:
        return ""

    df["sma20"] = df["close"].rolling(20).mean()
    df["sma50"] = df["close"].rolling(50).mean()
    if len(df) >= 100:
        df["sma200"] = df["close"].rolling(100).mean() # nếu khung 120 lấy sma100
    else:
        df["sma200"] = np.nan

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.5, 4.2), gridspec_kw={"height_ratios": [3, 1]}, sharex=True)
    fig.patch.set_facecolor("#FFFFFF")
    
    # 1. Đường giá và MA
    x_dates = df.index
    ax1.plot(x_dates, df["close"], label="Giá đóng cửa (VNĐ)", color=PRIMARY_COLOR, linewidth=1.8)
    ax1.plot(x_dates, df["sma20"], label="SMA 20", color="#DD6B20", linewidth=1.2, linestyle="--")
    ax1.plot(x_dates, df["sma50"], label="SMA 50", color="#319795", linewidth=1.2, linestyle="-.")
    if not df["sma200"].isna().all():
        ax1.plot(x_dates, df["sma200"], label="SMA 100/200", color="#805AD5", linewidth=1.2)
        
    ax1.set_title(f"XU HƯỚNG GIÁ & ĐƯỜNG TRUNG BÌNH ĐỘNG - {ticker}", fontsize=11, fontweight="bold", color=PRIMARY_COLOR, pad=10)
    ax1.set_ylabel("Giá (VNĐ)", fontsize=9, color="#4A5568")
    ax1.grid(True, linestyle=":", alpha=0.6, color=GRID_COLOR)
    ax1.legend(loc="upper left", framealpha=0.9, fontsize=8)
    ax1.tick_params(labelsize=8)
    ax1.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: f"{x:,.0f}"))

    # 2. Khối lượng giao dịch
    colors = [ACCENT_GREEN if c >= o else ACCENT_RED for c, o in zip(df["close"], df["open"])]
    ax2.bar(x_dates, df["volume"], color=colors, alpha=0.7, width=0.8)
    ax2.set_ylabel("Khối lượng", fontsize=8, color="#4A5568")
    ax2.grid(True, linestyle=":", alpha=0.5, color=GRID_COLOR)
    ax2.tick_params(labelsize=8)
    ax2.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: f"{x/1e6:.1f}M"))

    plt.xticks(rotation=15)
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=250, bbox_inches="tight")
    plt.close(fig)
    return str(output_path)

def generate_financial_performance_chart(history: List[Dict[str, Any]], ticker: str, output_path: Path) -> str:
    """
    Vẽ biểu đồ tăng trưởng Doanh thu, Lợi nhuận sau thuế và Biên lợi nhuận ròng qua các năm.
    """
    if not history or len(history) < 2:
        return ""

    years = [str(item["year"]) for item in history]
    revenue = [float(item.get("revenue", 0)) / 1000 for item in history] # Đơn vị: Nghìn tỷ VNĐ
    net_income = [float(item.get("net_income", 0)) / 1000 for item in history]
    net_margins = [(float(item.get("net_income", 0)) / float(item.get("revenue", 1))) * 100 if float(item.get("revenue", 0)) > 0 else 0 for item in history]

    fig, ax1 = plt.subplots(figsize=(8.0, 3.8))
    fig.patch.set_facecolor("#FFFFFF")
    
    x = np.arange(len(years))
    width = 0.32

    rects1 = ax1.bar(x - width/2, revenue, width, label="Doanh thu (Nghìn tỷ VNĐ)", color=SECONDARY_COLOR, alpha=0.9)
    rects2 = ax1.bar(x + width/2, net_income, width, label="LNST (Nghìn tỷ VNĐ)", color=ACCENT_GREEN, alpha=0.9)

    ax1.set_ylabel("Nghìn tỷ VNĐ", fontsize=9, color="#4A5568")
    ax1.set_title(f"TĂNG TRƯỞNG DOANH THU & LỢI NHUẬN THUẦN QUA CÁC NĂM - {ticker}", fontsize=11, fontweight="bold", color=PRIMARY_COLOR, pad=10)
    ax1.set_xticks(x)
    ax1.set_xticklabels(years, fontsize=9, fontweight="bold")
    ax1.grid(True, linestyle=":", alpha=0.5, color=GRID_COLOR, axis="y")
    ax1.tick_params(labelsize=8)

    # Thêm số liệu trên đầu cột
    for rect in rects1:
        h = rect.get_height()
        ax1.annotate(f"{h:.1f}", xy=(rect.get_x() + rect.get_width() / 2, h), xytext=(0, 2),
                    textcoords="offset points", ha="center", va="bottom", fontsize=7.5, color="#2D3748")
    for rect in rects2:
        h = rect.get_height()
        ax1.annotate(f"{h:.1f}", xy=(rect.get_x() + rect.get_width() / 2, h), xytext=(0, 2),
                    textcoords="offset points", ha="center", va="bottom", fontsize=7.5, fontweight="bold", color=ACCENT_GREEN)

    # Trục phụ biểu diễn biên lợi nhuận ròng
    ax2 = ax1.twinx()
    ax2.plot(x, net_margins, color="#E53E3E", marker="o", linewidth=1.8, label="Biên LN ròng (%)")
    ax2.set_ylabel("Biên LN ròng (%)", fontsize=9, color="#E53E3E")
    ax2.tick_params(axis="y", labelcolor="#E53E3E", labelsize=8)
    for i, txt in enumerate(net_margins):
        ax2.annotate(f"{txt:.1f}%", (x[i], net_margins[i]), textcoords="offset points", xytext=(0, 5), ha="center", fontsize=7.5, color="#E53E3E", fontweight="bold")

    # Ghép legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=8, framealpha=0.9)

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=250, bbox_inches="tight")
    plt.close(fig)
    return str(output_path)

def generate_scorecard_radar_chart(pillars: Dict[str, Any], ticker: str, output_path: Path) -> str:
    """
    Vẽ biểu đồ Radar (mạng nhện) 5 trụ cột của Quant Multi-Factor Scorecard.
    """
    labels = [v["label"] for v in pillars.values()]
    # Tính tỷ lệ % hoàn thành trên thang tối đa của từng trụ cột
    scores_pct = [(v["score"] / v["max"]) * 100 for v in pillars.values()]
    
    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    scores_pct += scores_pct[:1] # khép kín vòng
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(4.5, 4.5), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor("#FFFFFF")

    ax.plot(angles, scores_pct, color=SECONDARY_COLOR, linewidth=2, linestyle="solid")
    ax.fill(angles, scores_pct, color=SECONDARY_COLOR, alpha=0.25)

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_thetagrids(np.degrees(angles[:-1]), labels, fontsize=8, fontweight="bold", color="#2D3748")
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(["25%", "50%", "75%", "100%"], fontsize=7, color="#718096")
    ax.grid(True, linestyle=":", color="#CBD5E0")
    ax.set_title(f"QUANT MULTI-FACTOR SCORECARD - {ticker}", fontsize=10, fontweight="bold", color=PRIMARY_COLOR, pad=15)

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=250, bbox_inches="tight")
    plt.close(fig)
    return str(output_path)

def generate_scenario_valuation_chart(
    current_price: float,
    bull_target: float,
    base_target: float,
    bear_target: float,
    dcf_target: float,
    ticker: str,
    output_path: Path
) -> str:
    """
    Vẽ biểu đồ thanh ngang so sánh các kịch bản định giá Bear / Current / DCF / Base / Bull.
    """
    fig, ax = plt.subplots(figsize=(8.0, 3.2))
    fig.patch.set_facecolor("#FFFFFF")

    scenarios = [
        ("Kịch bản Tiêu cực (Bear)", bear_target, ACCENT_RED),
        ("Thị giá Hiện tại", current_price, "#4A5568"),
        ("Giá trị DCF (FCFF)", dcf_target, "#805AD5"),
        ("Kịch bản Cơ sở (Base)", base_target, SECONDARY_COLOR),
        ("Kịch bản Tích cực (Bull)", bull_target, ACCENT_GREEN)
    ]

    labels = [s[0] for s in scenarios]
    values = [s[1] for s in scenarios]
    colors = [s[2] for s in scenarios]

    y_pos = np.arange(len(labels))
    bars = ax.barh(y_pos, values, color=colors, height=0.55, alpha=0.9)

    # Kẻ đường dóng tại giá hiện tại
    ax.axvline(x=current_price, color="#4A5568", linestyle="--", linewidth=1.2, alpha=0.7)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8.5, fontweight="bold")
    ax.set_xlabel("Mức giá (VNĐ/cổ phiếu)", fontsize=9, color="#4A5568")
    ax.set_title(f"MA TRẬN ĐỊNH GIÁ & CÁC KỊCH BẢN ĐẦU TƯ 12 THÁNG - {ticker}", fontsize=11, fontweight="bold", color=PRIMARY_COLOR, pad=10)
    ax.grid(True, linestyle=":", alpha=0.5, color=GRID_COLOR, axis="x")
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: f"{x:,.0f}"))
    ax.tick_params(labelsize=8)

    # Thêm giá trị trên từng thanh
    for bar, val in zip(bars, values):
        upside = ((val - current_price) / current_price) * 100
        sign = "+" if upside > 0 else ""
        txt = f"{val:,.0f} ({sign}{upside:.1f}%)" if val != current_price else f"{val:,.0f} (Mốc cơ sở)"
        ax.annotate(txt, xy=(bar.get_width(), bar.get_y() + bar.get_height() / 2),
                    xytext=(5, 0), textcoords="offset points", ha="left", va="center",
                    fontsize=8, fontweight="bold", color="#1A202C")

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=250, bbox_inches="tight")
    plt.close(fig)
    return str(output_path)
