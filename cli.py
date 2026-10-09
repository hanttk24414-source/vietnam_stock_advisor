"""
Giao diện dòng lệnh (Command Line Interface - CLI) cho Hệ thống Phân tích Đầu tư Cổ phiếu Việt Nam.
Cho phép tự động phân tích và xuất báo cáo PDF hàng loạt hoặc theo mã chỉ định từ terminal.
Ví dụ:
    py cli.py --ticker HPG --timeframe 1y
    py cli.py --ticker FPT --output reports/FPT_Report.pdf
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Thiết lập UTF-8 stdout cho Windows
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from config import REPORTS_DIR, SUPPORTED_TICKERS
from data.macro_loader import fetch_macro_indicators, fetch_vnindex_history
from data.stock_loader import fetch_stock_price_history, fetch_stock_fundamentals, clean_ticker
from analytics.macro_engine import analyze_macro_environment
from analytics.industry_engine import evaluate_industry_and_peers
from analytics.technical_engine import compute_technical_indicators
from analytics.fundamental_engine import analyze_fundamentals
from analytics.valuation_engine import perform_valuation
from analytics.scorecard_engine import calculate_quant_scorecard, build_scenario_matrix
from reporting.pdf_generator import create_investment_report_pdf

def run_analysis(
    ticker: str,
    timeframe: str = "1y",
    output_filename: str = None,
    wacc: float = None,
    g: float = None,
    notes: str = None,
    demo: bool = False
) -> str:
    if not demo:
        raise RuntimeError('Chế độ THẬT chưa có nguồn dữ liệu vĩ mô xác minh. Dùng --demo cho bản trình diễn; không được dùng số liệu mẫu để đầu tư.')
    os.environ['STOCK_ADVISOR_DEMO'] = '1'
    ticker = clean_ticker(ticker)
    print(f"\n==================================================================")
    print(f" KHỞI CHẠY PHÂN TÍCH ĐẦU TƯ CỔ PHIẾU: {ticker}")
    print(f" Thời gian thực thi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"==================================================================")

    days_map = {"1y": 365, "3y": 1095, "5y": 1825}
    days = days_map.get(timeframe.lower(), 365)

    print("[1/5] Thu thập dữ liệu Vĩ mô & VN-Index...")
    macro_raw = fetch_macro_indicators()
    vnindex_df = fetch_vnindex_history(days)
    macro_res = analyze_macro_environment(macro_raw)
    print(f"      -> VN-Index: {macro_raw.get('vnindex_current', 0):,.1f} | ERP: {macro_raw.get('equity_risk_premium', 0):.2f}% ({macro_res.get('cycle_stage')})")

    print(f"[2/5] Thu thập dữ liệu giao dịch & BCTC của {ticker}...")
    price_df = fetch_stock_price_history(ticker, days)
    stock_raw = fetch_stock_fundamentals(ticker)
    print(f"      -> Doanh nghiệp: {stock_raw.get('name')} | Ngành: {stock_raw.get('sector')}")
    print(f"      -> Số phiên giao dịch đã tải: {len(price_df)} | BCTC: {len(stock_raw.get('financial_history', []))} năm")

    print("[3/5] Thực thi các thuật toán phân tích Kỹ thuật, Cơ bản, DuPont...")
    tech_res = compute_technical_indicators(price_df, vnindex_df)
    fund_res = analyze_fundamentals(stock_raw)
    ind_res = evaluate_industry_and_peers(stock_raw.get("sector_code", "STEEL"), stock_raw)
    print(f"      -> Tín hiệu Kỹ thuật: {tech_res.get('overall_signal')} (RSI: {tech_res.get('rsi', 0):.1f})")
    print(f"      -> Hiệu quả: ROE {fund_res.get('roe'):.1f}% | Biên ròng {fund_res.get('net_margin'):.1f}% | D/E {fund_res.get('debt_to_equity'):.2f}x")

    print("[4/5] Định giá đa mô hình & Chấm điểm Quant Multi-Factor...")
    val_res = perform_valuation(
        stock_raw,
        fund_res,
        ind_res,
        beta=tech_res.get("beta", 1.1),
        custom_wacc=wacc,
        custom_g=g
    )
    score_res = calculate_quant_scorecard(fund_res, tech_res, val_res, ind_res, macro_res)
    scen_res = build_scenario_matrix(val_res["current_price"], val_res["blended_target_price"], fund_res, tech_res)
    
    cur_p = val_res["current_price"]
    tgt_p = val_res["blended_target_price"]
    upside = val_res["blended_upside"]
    rating = score_res["rating"]
    score = score_res["total_score"]

    print(f"      -> Thị giá: {cur_p:,.0f} đ | Giá mục tiêu 12T: {tgt_p:,.0f} đ (+{upside:.1f}%)")
    print(f"      -> Định giá P/E: {val_res['pe_fair_value']:,.0f} đ | P/B: {val_res['pb_fair_value']:,.0f} đ | DCF: {val_res['dcf_fair_value']:,.0f} đ")
    print(f"      -> Quant Scorecard: {score:.1f}/100 -> KHUYẾN NGHỊ: {rating}")
    print(f"      -> Kịch bản Bull: {scen_res['bull_case']['target_price']:,.0f} đ | Base: {scen_res['base_case']['target_price']:,.0f} đ | Bear: {scen_res['bear_case']['target_price']:,.0f} đ")

    print("[5/5] Đang tạo báo cáo phân tích đầu tư PDF chuyên nghiệp...")
    if output_filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"DEMO_BaoCao_{ticker}_{timestamp}.pdf"

    pdf_path = create_investment_report_pdf(
        ticker=ticker,
        stock_fundamentals=stock_raw,
        fundamental_analysis=fund_res,
        technical_analysis=tech_res,
        valuation_analysis=val_res,
        scorecard_analysis=score_res,
        scenario_analysis=scen_res,
        macro_analysis=macro_res,
        industry_analysis=ind_res,
        price_df=price_df,
        output_filename=output_filename,
        analysis_date=datetime.now().strftime("%d/%m/%Y"),
        custom_notes="CHẾ ĐỘ DEMO - KHÔNG DÙNG ĐẦU TƯ. " + (notes or "")
    )

    print(f"\n✅ HOÀN TẤT! File báo cáo PDF đã được lưu thành công tại:")
    print(f"   -> {pdf_path}")
    print(f"==================================================================\n")
    return pdf_path

def main():
    parser = argparse.ArgumentParser(description="Hệ thống Phân tích Cơ hội Đầu tư Cổ phiếu Việt Nam & Xuất PDF")
    parser.add_argument("--ticker", type=str, default="HPG", help="Mã cổ phiếu phân tích (ví dụ: HPG, FPT, VCB)")
    parser.add_argument("--timeframe", type=str, default="1y", choices=["1y", "3y", "5y"], help="Khung thời gian lịch sử giá")
    parser.add_argument("--output", type=str, default=None, help="Tên file PDF xuất ra")
    parser.add_argument("--wacc", type=float, default=None, help="Chi phí vốn bình quân WACC (ví dụ: 0.085 cho 8.5%)")
    parser.add_argument("--g", type=float, default=None, help="Tốc độ tăng trưởng dài hạn vĩnh viễn (ví dụ: 0.035 cho 3.5%)")
    parser.add_argument("--notes", type=str, default=None, help="Ghi chú thêm của chuyên viên phân tích")
    
    parser.add_argument("--demo", action="store_true", help="Chỉ trình diễn với dữ liệu mẫu, không dùng để đầu tư")
    args = parser.parse_args()
    run_analysis(
        ticker=args.ticker,
        timeframe=args.timeframe,
        output_filename=args.output,
        wacc=args.wacc,
        g=args.g,
        notes=args.notes,
        demo=args.demo
    )

if __name__ == "__main__":
    main()
