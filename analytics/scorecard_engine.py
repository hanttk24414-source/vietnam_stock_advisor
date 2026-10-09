"""
Module chấm điểm cơ hội đầu tư định lượng (Quant Multi-Factor Scorecard)
và xây dựng ma trận kịch bản đầu tư (Scenario Matrix).
Bao gồm:
1. Hệ thống chấm điểm 5 trụ cột (Tổng 100 điểm): Tăng trưởng, Chất lượng, Tài chính, Định giá, Kỹ thuật.
2. Ma trận 3 kịch bản: Tích cực (Bull Case), Cơ sở (Base Case), Tiêu cực (Bear Case).
3. Luận điểm đầu tư (Investment Theses), Điều kiện kích hoạt và Ngưỡng dừng lỗ bảo toàn vốn.
"""

from typing import Dict, Any, List
from config import RATING_SCALE, SCORECARD_WEIGHTS
from analytics.recommendation_engine import build_recommendation

def calculate_quant_scorecard(
    fundamental_analysis: Dict[str, Any],
    technical_analysis: Dict[str, Any],
    valuation_analysis: Dict[str, Any],
    industry_analysis: Dict[str, Any],
    macro_analysis: Dict[str, Any],
    ticker: str = "",
    price_status: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Tính toán bảng điểm định lượng toàn diện 100 điểm với giải thích chi tiết.
    """
    ticker = ticker or fundamental_analysis.get("ticker", "Cổ phiếu")
    if not fundamental_analysis.get("available", True) or fundamental_analysis.get("missing_fields"):
        result = build_recommendation(ticker, technical_analysis, fundamental_analysis,
                                      valuation_analysis, price_status=price_status)
        result.update(total_score=None, pillars={}, strengths=result["evidence"])
        return result
    strengths: List[str] = []
    risks: List[str] = []

    # 1. Trụ cột Tăng trưởng (Max 20 điểm)
    growth_score = 0.0
    rev_growth = fundamental_analysis.get("rev_growth_yoy", 0.0)
    ni_growth = fundamental_analysis.get("ni_growth_yoy", 0.0)
    rev_cagr = fundamental_analysis.get("rev_cagr_3y", 0.0)

    if rev_growth >= 25.0:
        growth_score += 8.0
        strengths.append(f"Doanh thu tăng trưởng vượt bậc +{rev_growth:.1f}% YoY so với kỳ báo cáo trước.")
    elif rev_growth >= 12.0:
        growth_score += 6.0
        strengths.append(f"Doanh thu tăng trưởng ổn định +{rev_growth:.1f}% YoY.")
    elif rev_growth > 0:
        growth_score += 4.0
    else:
        risks.append(f"Tăng trưởng doanh thu suy giảm {rev_growth:.1f}% YoY.")

    if ni_growth >= 20.0:
        growth_score += 8.0
        strengths.append(f"Lợi nhuận ròng tăng trưởng ấn tượng +{ni_growth:.1f}% YoY.")
    elif ni_growth >= 10.0:
        growth_score += 6.0
    elif ni_growth > 0:
        growth_score += 3.0
    else:
        risks.append(f"Lợi nhuận suy giảm {ni_growth:.1f}% YoY trong kỳ báo cáo gần nhất.")

    if rev_cagr >= 15.0:
        growth_score += 4.0
    elif rev_cagr >= 8.0:
        growth_score += 2.5
    else:
        growth_score += 1.0

    growth_score = min(20.0, growth_score)

    # 2. Trụ cột Khả năng sinh lời & Chất lượng kinh doanh (Max 25 điểm)
    quality_score = 0.0
    roe = fundamental_analysis.get("roe", 0.0)
    roa = fundamental_analysis.get("roa", 0.0)
    net_margin = fundamental_analysis.get("net_margin", 0.0)
    cf_quality_score = fundamental_analysis.get("cf_quality_score", 70.0)

    if roe >= 20.0:
        quality_score += 8.0
        strengths.append(f"Tỷ suất ROE đạt {roe:.1f}%, theo BCTC của doanh nghiệp.")
    elif roe >= 15.0:
        quality_score += 6.5
        strengths.append(f"Tỷ suất ROE đạt {roe:.1f}%, vượt trội so với lãi suất tiền gửi.")
    elif roe >= 10.0:
        quality_score += 4.0
    else:
        risks.append(f"Tỷ suất sinh lời trên vốn chủ ROE ở mức khiêm tốn {roe:.1f}%.")

    if roa >= 10.0:
        quality_score += 5.0
    elif roa >= 6.0:
        quality_score += 4.0
    else:
        quality_score += 2.0

    if net_margin >= 15.0:
        quality_score += 5.0
        strengths.append(f"Biên lợi nhuận ròng cao ({net_margin:.1f}%) theo BCTC kỳ gần nhất.")
    elif net_margin >= 8.0:
        quality_score += 4.0
    else:
        quality_score += 2.0

    # Chất lượng dòng tiền đóng góp tối đa 7 điểm
    quality_score += (cf_quality_score / 100.0) * 7.0
    if fundamental_analysis.get("ocf_to_ni_ratio", 0.0) >= 1.0:
        strengths.append("Dòng tiền thuần kinh doanh OCF vượt lợi nhuận sau thuế, chất lượng dòng tiền xuất sắc.")
    else:
        risks.append("Dòng tiền kinh doanh cần theo dõi thêm do chu kỳ lưu kho và vốn lưu động.")

    quality_score = min(25.0, quality_score)

    # 3. Trụ cột Sức khỏe tài chính & Đòn bẩy (Max 20 điểm)
    fin_health_score = 0.0
    dte = fundamental_analysis.get("debt_to_equity", 0.65)
    
    if dte <= 0.6:
        fin_health_score += 10.0
        strengths.append(f"Đòn bẩy tài chính rất thấp (D/E: {dte:.2f}x), cần đối chiếu với cơ cấu kỳ hạn nợ.")
    elif dte <= 1.0:
        fin_health_score += 8.0
        strengths.append(f"Tỷ lệ nợ trên vốn chủ D/E đạt {dte:.2f}x theo BCTC kỳ gần nhất.")
    elif dte <= 1.8:
        fin_health_score += 5.0
    else:
        fin_health_score += 2.0
        risks.append(f"Đòn bẩy tài chính D/E ở mức {dte:.2f}x, cần lưu ý áp lực chi phí lãi vay.")

    # Điểm đánh giá dòng tiền / nợ ròng
    fin_health_score += (fundamental_analysis.get("health_score", 75.0) / 100.0) * 10.0
    fin_health_score = min(20.0, fin_health_score)

    # 4. Trụ cột Sức hấp dẫn định giá (Max 20 điểm)
    val_score = 0.0
    upside = valuation_analysis.get("blended_upside", 0.0)
    pe_discount = industry_analysis.get("pe_discount_pct", 0.0)
    
    if upside >= 30.0:
        val_score += 10.0
        strengths.append(f"Giá mục tiêu tổng hợp cao hơn thị giá hiện tại +{upside:.1f}%, biên an toàn lớn.")
    elif upside >= 15.0:
        val_score += 7.5
        strengths.append(f"Biên tăng giá kỳ vọng hấp dẫn +{upside:.1f}%.")
    elif upside > 0:
        val_score += 4.5
    else:
        val_score += 1.0
        risks.append("Thị giá hiện tại đã phản ánh phần lớn tiềm năng định giá ngắn hạn.")

    if pe_discount >= 20.0:
        val_score += 7.0
        strengths.append(f"P/E chiết khấu {pe_discount:.1f}% so với P/E trung bình ngành.")
    elif pe_discount >= 0:
        val_score += 5.0
    else:
        val_score += 2.0

    # Điểm cộng từ ERP vĩ mô
    if macro_analysis.get("equity_risk_premium", 0.0) >= 3.0:
        val_score += 3.0

    val_score = min(20.0, val_score)

    # 5. Trụ cột Kỹ thuật & Động lượng (Max 15 điểm)
    tech_score_raw = technical_analysis.get("tech_score", 50.0)
    tech_pillar_score = round((tech_score_raw / 100.0) * 15.0, 1)
    
    if technical_analysis.get("overall_signal") == "TÍCH CỰC (BULLISH)":
        strengths.append("Đồ thị kỹ thuật duy trì trên các đường trung bình MA20/MA50, xu hướng tăng chủ đạo.")
    elif technical_analysis.get("overall_signal") == "TIÊU CỰC (BEARISH)":
        risks.append("Áp lực bán kỹ thuật đang chi phối, cổ phiếu dưới các đường kháng cự động.")

    # Tổng điểm quy chuẩn (Thang 100)
    total_score = round(growth_score + quality_score + fin_health_score + val_score + tech_pillar_score, 1)

    # Xác định xếp hạng theo thang điểm chuẩn
    rating_title = "NẮM GIỮ (HOLD)"
    action_guide = "Duy trì vị thế hiện tại, quan sát thêm tín hiệu xác nhận"
    for item in RATING_SCALE:
        if item["min_score"] <= total_score <= item["max_score"]:
            rating_title = item["rating"]
            action_guide = item["action"]
            break

    pillars = {
        "growth": {"score": round(growth_score, 1), "max": 20, "label": "Tăng trưởng"},
        "profitability": {"score": round(quality_score, 1), "max": 25, "label": "Khả năng sinh lời & Chất lượng"},
        "financial_health": {"score": round(fin_health_score, 1), "max": 20, "label": "Sức khỏe tài chính & Đòn bẩy"},
        "valuation": {"score": round(val_score, 1), "max": 20, "label": "Định giá hấp dẫn"},
        "technical": {"score": tech_pillar_score, "max": 15, "label": "Động lượng kỹ thuật"}
    }

    recommendation = build_recommendation(ticker, technical_analysis, fundamental_analysis,
                                          valuation_analysis, total_score, price_status)
    rating_title = recommendation["rating"]
    action_guide = recommendation["action_guide"]
    return {
        **recommendation,
        "total_score": total_score,
        "rating": rating_title,
        "action_guide": action_guide,
        "pillars": pillars,
        "strengths": strengths,
        "risks": list(dict.fromkeys(risks + recommendation["risks"]))
    }

def build_scenario_matrix(
    current_price: float,
    blended_target: float,
    fundamental_analysis: Dict[str, Any],
    technical_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Xây dựng ma trận 3 kịch bản đầu tư (Bull / Base / Bear Case) kèm xác suất và tỷ lệ Lợi nhuận / Rủi ro.
    """
    if current_price <= 0 or blended_target <= 0:
        raise ValueError("Kịch bản cần giá và giá mục tiêu dương.")
    ticker = fundamental_analysis.get("ticker", "Cổ phiếu")
    # 1. Kịch bản Cơ sở (Base Case - 55% xác suất): Đạt giá trị định giá tổng hợp
    base_target = blended_target
    base_upside = round(((base_target - current_price) / current_price) * 100, 1)

    # 2. Kịch bản Tích cực (Bull Case - 25% xác suất): Kết quả kinh doanh vượt kỳ vọng + P/E mở rộng
    bull_target = round(blended_target * 1.18, 0)
    bull_upside = round(((bull_target - current_price) / current_price) * 100, 1)

    # 3. Kịch bản Thận trọng (Bear Case - 20% xác suất): Rủi ro vĩ mô/ngành phát sinh, kiểm tra lại đáy kỹ thuật
    support_2 = technical_analysis.get("support_levels", [current_price * 0.9, current_price * 0.85])[1]
    bear_target = round(min(support_2, current_price * 0.85, blended_target * 0.85), 0)
    bear_downside = round(((bear_target - current_price) / current_price) * 100, 1)

    # Giá trị kỳ vọng theo xác suất (Probability-Weighted Fair Value)
    prob_bull = 0.25
    prob_base = 0.55
    prob_bear = 0.20
    weighted_target = round((bull_target * prob_bull) + (base_target * prob_base) + (bear_target * prob_bear), 0)
    weighted_upside = round(((weighted_target - current_price) / current_price) * 100, 1)

    # Tỷ lệ Lợi nhuận / Rủi ro (Risk-Reward Ratio)
    potential_gain = max(1.0, bull_target - current_price)
    potential_loss = max(1.0, current_price - bear_target)
    risk_reward_ratio = round(potential_gain / potential_loss, 2)

    # Ngưỡng Dừng lỗ Bảo toàn vốn (Stop-loss level: vi phạm MA50 hoặc giảm 7-8% từ giá mua)
    stop_loss_price = round(min(current_price * 0.925, bear_target), 0)
    supports = [x for x in technical_analysis.get("support_levels", []) if 0 < x < current_price]
    support = max(supports) if supports else current_price * 0.95
    buy_zone = f"Vùng hỗ trợ tham chiếu {support:,.0f} VNĐ; chỉ cân nhắc mua nếu khuyến nghị và điều kiện xác nhận phù hợp"

    return {
        "assumption_notice": "Biên kịch bản và xác suất 25/55/20 là giả định minh họa, chưa được hiệu chỉnh bằng backtest.",
        "current_price": current_price,
        "bull_case": {
            "target_price": bull_target,
            "upside_pct": bull_upside,
            "probability": prob_bull,
            "assumptions": f"{ticker}: giả định giá mục tiêu cơ sở tăng 18%; cần lợi nhuận cải thiện và giá vượt kháng cự {technical_analysis.get('resistance_levels', [current_price])[0]:,.0f} đ."
        },
        "base_case": {
            "target_price": base_target,
            "upside_pct": base_upside,
            "probability": prob_base,
            "assumptions": f"{ticker}: giữ giả định định giá; tăng trưởng doanh thu tham chiếu {fundamental_analysis.get('rev_growth_yoy', 0):+.1f}%, ROE {fundamental_analysis.get('roe', 0):.1f}%."
        },
        "bear_case": {
            "target_price": bear_target,
            "downside_pct": bear_downside,
            "probability": prob_bear,
            "assumptions": f"{ticker}: mất hỗ trợ {support_2:,.0f} đ hoặc lợi nhuận suy yếu; biên ròng tham chiếu {fundamental_analysis.get('net_margin', 0):.1f}%."
        },
        "weighted_target_price": weighted_target,
        "weighted_upside_pct": weighted_upside,
        "risk_reward_ratio": risk_reward_ratio,
        "recommended_buy_zone": buy_zone,
        "stop_loss_price": stop_loss_price
    }

