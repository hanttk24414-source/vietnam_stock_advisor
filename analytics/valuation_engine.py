"""
Module định giá cổ phiếu đa phương pháp:
1. Phương pháp P/E mục tiêu.
2. Phương pháp P/B mục tiêu.
3. Phương pháp Chiết khấu Dòng tiền Tự do (DCF 2 giai đoạn FCFF).
4. Phương pháp EV/EBITDA.
5. Giá trị mục tiêu tổng hợp (Blended Fair Value), Biên an toàn và Upside tiềm năng.
"""

from typing import Dict, Any
from config import MACRO_DEFAULTS

def perform_valuation(
    stock_fundamentals: Dict[str, Any],
    fundamental_analysis: Dict[str, Any],
    industry_analysis: Dict[str, Any],
    beta: float = 1.1,
    custom_wacc: float = None,
    custom_g: float = None
) -> Dict[str, Any]:
    """
    Thực hiện định giá tài chính chuẩn mực theo nhiều phương pháp và tổng hợp giá mục tiêu 12 tháng.
    """
    if not fundamental_analysis.get("available", True):
        raise ValueError("Chưa có BCTC đủ để định giá.")
    if stock_fundamentals.get("shares_outstanding", 0) <= 0:
        raise ValueError("Chưa có số cổ phiếu lưu hành từ nguồn dữ liệu.")
    if industry_analysis.get("benchmark_pe", 0) <= 0 or industry_analysis.get("benchmark_pb", 0) <= 0:
        raise ValueError("Chưa có giả định định giá phù hợp với ngành này.")
    current_price = stock_fundamentals.get("current_price", 20000.0)
    shares = stock_fundamentals.get("shares_outstanding", 1_000_000_000)
    sector_code = stock_fundamentals.get("sector_code", "STEEL")
    
    eps = fundamental_analysis.get("eps", 2500.0)
    bvps = fundamental_analysis.get("bvps", 18000.0)
    fcf_latest = fundamental_analysis.get("fcf_bil", 5000.0)
    net_debt = fundamental_analysis.get("net_debt_bil", 20000.0)
    
    bench_pe = industry_analysis.get("benchmark_pe", 12.0)
    bench_pb = industry_analysis.get("benchmark_pb", 1.4)
    
    # 1. Định giá theo P/E
    # Áp dụng P/E mục tiêu hài hòa giữa trung bình ngành và lịch sử
    target_pe = bench_pe * 0.95
    pe_available = eps > 0
    pe_fair_value = round(eps * target_pe, 0) if pe_available else 0
    pe_upside = round(((pe_fair_value - current_price) / current_price) * 100, 1)

    # 2. Định giá theo P/B
    target_pb = bench_pb * 0.95
    pb_fair_value = round(bvps * target_pb, 0)
    pb_upside = round(((pb_fair_value - current_price) / current_price) * 100, 1)

    # 3. Định giá Chiết khấu Dòng tiền (DCF FCFF 2-Stage)
    # Tính WACC
    rf = MACRO_DEFAULTS["risk_free_rate"]
    erp = MACRO_DEFAULTS["equity_risk_premium"]
    tax_rate = MACRO_DEFAULTS["corporate_tax_rate"]
    g_terminal = custom_g if custom_g is not None else MACRO_DEFAULTS["terminal_growth_rate"]
    
    # Chi phí vốn cổ phần Ke (CAPM)
    ke = rf + beta * erp
    # Chi phí nợ vay sau thuế Kd
    kd_before_tax = 0.075  # Lãi suất vay doanh nghiệp lớn ~ 7.5%
    kd = kd_before_tax * (1 - tax_rate)
    
    # Cơ cấu vốn E/V và D/V
    dte = fundamental_analysis.get("debt_to_equity", 0.65)
    e_weight = 1.0 / (1.0 + dte)
    d_weight = dte / (1.0 + dte)
    
    calc_wacc = (e_weight * ke) + (d_weight * kd)
    wacc = custom_wacc if custom_wacc is not None else max(0.085, calc_wacc)

    # Dự phóng FCFF 5 năm
    # Không đưa DCF vào kết quả khi FCF âm hoặc thiếu dữ liệu.
    base_fcf = fcf_latest
    dcf_available = (base_fcf > 0 and sector_code not in ["BANKING", "BROKERAGE"]
                     and not fundamental_analysis.get("missing_fields"))

    growth_anchor = max(-0.05, min(0.20, fundamental_analysis.get("rev_cagr_3y", 0) / 100))
    growth_rates = [growth_anchor + (g_terminal - growth_anchor) * i / 5 for i in range(5)]
    projected_fcf = []
    pv_fcf = 0.0
    cur_fcf = base_fcf
    
    for i, g in enumerate(growth_rates, start=1):
        cur_fcf = cur_fcf * (1 + g)
        discount_factor = (1 + wacc) ** i
        pv = cur_fcf / discount_factor
        pv_fcf += pv
        projected_fcf.append({"year": f"Y+{i}", "fcf": round(cur_fcf, 1), "pv": round(pv, 1)})

    # Terminal Value tại năm thứ 5
    fcf_terminal = cur_fcf * (1 + g_terminal)
    denom = max(0.015, wacc - g_terminal)
    terminal_value = fcf_terminal / denom
    pv_terminal_value = terminal_value / ((1 + wacc) ** 5)

    enterprise_value = pv_fcf + pv_terminal_value
    equity_value = enterprise_value - net_debt
    dcf_fair_value = round((equity_value * 1e9) / shares, 0) if shares > 0 else current_price * 1.15
    dcf_fair_value = max(0, dcf_fair_value) if dcf_available else 0
    dcf_upside = round(((dcf_fair_value - current_price) / current_price) * 100, 1)

    # 4. Trọng số tổng hợp (Blended Fair Value)
    if sector_code in ["BANKING", "BROKERAGE"] or not dcf_available:
        # Ngân hàng không áp dụng DCF FCFF
        weights = {"pe": 0.45, "pb": 0.55, "dcf": 0.0}
        blended_target = round((pe_fair_value * 0.45) + (pb_fair_value * 0.55), 0)
    else:
        weights = {"pe": 0.30, "pb": 0.30, "dcf": 0.40}
        blended_target = round((pe_fair_value * 0.30) + (pb_fair_value * 0.30) + (dcf_fair_value * 0.40), 0)

    if not pe_available:
        weights = {"pe": 0.0, "pb": 1.0, "dcf": 0.0}
        blended_target = pb_fair_value
    if blended_target <= 0:
        raise ValueError("Mô hình chưa có giá mục tiêu dương hợp lệ.")
    blended_upside = round(((blended_target - current_price) / current_price) * 100, 1)
    margin_of_safety = round(blended_upside, 1) if blended_upside > 0 else 0.0

    return {
        "benchmark_source": industry_analysis.get("benchmark_source", "Giả định tham chiếu"),
        "available": True,
        "dcf_available": dcf_available,
        "pe_available": pe_available,
        "assumptions": "P/E và P/B ngành là giả định tham chiếu; DCF dùng OCF−CapEx làm xấp xỉ dòng tiền, chưa phải FCFF chuẩn hóa.",
        "current_price": current_price,
        "pe_fair_value": pe_fair_value,
        "pe_upside": pe_upside,
        "pb_fair_value": pb_fair_value,
        "pb_upside": pb_upside,
        "dcf_fair_value": dcf_fair_value,
        "dcf_upside": dcf_upside,
        "blended_target_price": blended_target,
        "blended_upside": blended_upside,
        "margin_of_safety": margin_of_safety,
        "wacc": round(wacc * 100, 2),
        "cost_of_equity": round(ke * 100, 2),
        "cost_of_debt": round(kd * 100, 2),
        "terminal_growth": round(g_terminal * 100, 2),
        "enterprise_value_bil": round(enterprise_value, 1),
        "pv_fcf_sum_bil": round(pv_fcf, 1),
        "pv_tv_bil": round(pv_terminal_value, 1),
        "projected_fcf": projected_fcf,
        "method_weights": weights
    }

