"""
Module phân tích tổng quan kinh tế vĩ mô và tác động đến TTCK Việt Nam.
Đánh giá:
1. Chu kỳ kinh tế và môi trường lãi suất / lạm phát / tỷ giá.
2. Định giá VN-Index và Lợi suất thị trường (Earnings Yield).
3. Phần bù rủi ro vốn cổ phần (Equity Risk Premium - ERP).
4. Khuyến nghị phân bổ tài sản vĩ mô.
"""

from typing import Dict, Any

def analyze_macro_environment(macro_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phân tích định lượng và định tính môi trường kinh tế vĩ mô Việt Nam.
    """
    gdp_growth = macro_data.get("gdp_growth_latest_quarter", 7.4)
    cpi = macro_data.get("cpi_yoy", 3.45)
    refinancing_rate = macro_data.get("refinancing_rate", 4.5)
    usd_vnd = macro_data.get("usd_vnd_rate", 25889.0)
    vnindex = macro_data.get("vnindex_current", 1740.0)
    pe = macro_data.get("vnindex_pe", 14.8)
    erp = macro_data.get("equity_risk_premium", 3.56)
    bond_10y = macro_data.get("gov_bond_10y_yield", 3.20)
    
    # 1. Xác định giai đoạn chu kỳ kinh tế
    if gdp_growth >= 6.5 and cpi <= 4.0:
        cycle_stage = "Mở rộng & Tăng trưởng Cao (Goldilocks Expansion)"
        cycle_desc = "Tăng trưởng GDP vượt kỳ vọng trong khi lạm phát được kiểm soát dưới ngưỡng mục tiêu 4.0%."
    elif gdp_growth >= 5.5 and cpi > 4.5:
        cycle_stage = "Tăng trưởng chậm kèm Áp lực Lạm phát (Late Cycle)"
        cycle_desc = "Kinh tế mở rộng nhưng chịu áp lực lạm phát chi phí đẩy."
    elif gdp_growth < 5.0 and cpi <= 3.5:
        cycle_stage = "Phục hồi Sơ khởi (Early Recovery)"
        cycle_desc = "Kinh tế tạo đáy và bắt đầu đón nhận các gói kích thích tài khóa và nới lỏng tiền tệ."
    else:
        cycle_stage = "Tăng trưởng Cân bằng (Steady Growth)"
        cycle_desc = "Kinh tế tăng trưởng ổn định trong tầm kiểm soát của chính sách tiền tệ."

    # 2. Đánh giá chính sách tiền tệ của NHNN
    if refinancing_rate <= 4.5:
        monetary_stance = "Thích ứng & Hỗ trợ Thanh khoản (Accommodative)"
        monetary_detail = "Mặt bằng lãi suất điều hành duy trì ở vùng thấp lịch sử nhằm hỗ trợ dòng vốn cho doanh nghiệp sản xuất và kích cầu tiêu dùng."
    elif refinancing_rate <= 5.5:
        monetary_stance = "Trung tính (Neutral)"
        monetary_detail = "Lãi suất cân bằng giữa hỗ trợ tăng trưởng và kiểm soát ổn định tỷ giá."
    else:
        monetary_stance = "Thắt chặt (Tightening)"
        monetary_detail = "Ưu tiên hàng đầu là kiềm chế lạm phát và hạ nhiệt tỷ giá USD/VND."

    # 3. Đánh giá sức hấp dẫn định giá thị trường qua ERP
    # ERP = Earning Yield - Bond Yield
    if erp >= 3.5:
        equity_attractiveness = "RẤT HẤP DẪN - KÊNH ĐẦU TƯ CỔ PHIẾU VƯỢT TRỘI SO VỚI TIỀN GỬI & TRÁI PHIẾU"
        recommended_equity_weight = "70% - 85% Cổ phiếu / 15% - 30% Tiền mặt & Công cụ Lãi suất"
    elif erp >= 2.0:
        equity_attractiveness = "HẤP DẪN VỪA PHẢI - ƯU TIÊN LỰA CHỌN CỔ PHIẾU ĐẦU NGÀNH"
        recommended_equity_weight = "55% - 70% Cổ phiếu / 30% - 45% Tiền mặt"
    else:
        equity_attractiveness = "THẬN TRỌNG - ĐỊNH GIÁ THỊ TRƯỜNG KHÔNG CÒN RẺ"
        recommended_equity_weight = "40% - 50% Cổ phiếu / 50% - 60% Tiền mặt & Trái phiếu"

    # 4. Tổng hợp các yếu tố xúc tác và rủi ro vĩ mô
    key_catalysts = [
        "Quyết tâm nâng hạng thị trường chứng khoán Việt Nam lên FTSE Emerging Market mở ra dòng vốn ngoại hàng tỷ USD.",
        "Mặt bằng lãi suất cho vay thương mại 6.5% - 8.5% duy trì mức thấp nhất trong nhiều năm kích hoạt nhu cầu đầu tư tư nhân.",
        "Tiến độ giải ngân vốn đầu tư công hạ tầng giao thông trọng điểm thúc đẩy tăng trưởng liên ngành.",
        "Dòng vốn FDI giải ngân thực tế tăng trưởng ổn định khẳng định vị thế cứ điểm sản xuất chiến lược toàn cầu."
    ]

    key_risks = [
        "Biến động tỷ giá USD/VND nếu chỉ số DXY tăng mạnh khiến NHNN phải can thiệp hút ròng tiền đồng qua tín phiếu.",
        "Rủi ro địa chính trị toàn cầu và gián đoạn chuỗi cung ứng hàng hải đẩy chi phí logistics lên cao.",
        "Áp lực đáo hạn trái phiếu doanh nghiệp trong nước của nhóm doanh nghiệp bất động sản dòng tiền yếu."
    ]

    return {
        "cycle_stage": cycle_stage,
        "cycle_desc": cycle_desc,
        "monetary_stance": monetary_stance,
        "monetary_detail": monetary_detail,
        "equity_attractiveness": equity_attractiveness,
        "recommended_equity_weight": recommended_equity_weight,
        "vnindex_pe": pe,
        "market_earnings_yield": round((1.0 / pe) * 100, 2) if pe > 0 else 6.76,
        "bond_10y_yield": bond_10y,
        "equity_risk_premium": erp,
        "macro_score": macro_data.get("macro_score", 80),
        "key_catalysts": key_catalysts,
        "key_risks": key_risks
    }
