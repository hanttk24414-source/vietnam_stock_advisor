"""
Cấu hình hệ thống Phân tích Cơ hội Đầu tư Cổ phiếu Việt Nam
Vietnam Stock Investment Analysis & Automated Reporting System
"""

import os
from pathlib import Path

# Thư mục gốc dự án
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
REPORTS_DIR = BASE_DIR / "reports"
STATIC_DIR = BASE_DIR / "static"

for directory in [CACHE_DIR, REPORTS_DIR, STATIC_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Danh sách mã cổ phiếu theo dõi trọng điểm theo từng ngành
SUPPORTED_TICKERS = {
    "HPG": {
        "name": "CTCP Tập đoàn Hòa Phát",
        "exchange": "HOSE",
        "sector": "Thép & Vật liệu xây dựng",
        "sector_code": "STEEL",
        "yf_ticker": "HPG.VN",
        "shares_outstanding": 7_280_000_000,
        "description": "Nhà sản xuất thép hàng đầu Đông Nam Á với chuỗi giá trị khép kín và dự án Dung Quất 2."
    },
    "FPT": {
        "name": "CTCP FPT",
        "exchange": "HOSE",
        "sector": "Công nghệ thông tin & Viễn thông",
        "sector_code": "TECH",
        "yf_ticker": "FPT.VN",
        "shares_outstanding": 1_460_000_000,
        "description": "Tập đoàn công nghệ hàng đầu Việt Nam tiên phong trong chuyển đổi số, AI và bán dẫn."
    },
    "VCB": {
        "name": "Ngân hàng TMCP Ngoại thương Việt Nam (Vietcombank)",
        "exchange": "HOSE",
        "sector": "Ngân hàng",
        "sector_code": "BANKING",
        "yf_ticker": "VCB.VN",
        "shares_outstanding": 5_589_000_000,
        "description": "Ngân hàng thương mại hàng đầu Việt Nam với chất lượng tài sản tốt nhất hệ thống và thế mạnh thanh toán quốc tế."
    },
    "MWG": {
        "name": "CTCP Đầu tư Thế Giới Di Động",
        "exchange": "HOSE",
        "sector": "Bán lẻ & Tiêu dùng",
        "sector_code": "RETAIL",
        "yf_ticker": "MWG.VN",
        "shares_outstanding": 1_462_000_000,
        "description": "Tập đoàn bán lẻ số 1 Việt Nam sở hữu chuỗi Thế Giới Di Động, Điện Máy Xanh, Bách Hóa Xanh và An Khang."
    },
    "SSI": {
        "name": "CTCP Chứng khoán SSI",
        "exchange": "HOSE",
        "sector": "Dịch vụ Tài chính & Chứng khoán",
        "sector_code": "BROKERAGE",
        "yf_ticker": "SSI.VN",
        "shares_outstanding": 1_964_000_000,
        "description": "Công ty chứng khoán hàng đầu thị trường với quy mô vốn, thị phần môi giới và năng lực tư vấn vượt trội."
    },
    "VHM": {
        "name": "CTCP Vinhomes",
        "exchange": "HOSE",
        "sector": "Bất động sản Dân dụng",
        "sector_code": "REAL_ESTATE",
        "yf_ticker": "VHM.VN",
        "shares_outstanding": 4_354_000_000,
        "description": "Nhà phát triển bất động sản số 1 Việt Nam với quỹ đất lớn nhất và năng lực triển khai các đại đô thị phức hợp."
    }
}

# Tham số mô hình Vĩ mô & Định giá tài chính (Vietnam Market Parameters)
MACRO_DEFAULTS = {
    "risk_free_rate": 0.032,       # Lợi suất TPCP 10 năm Việt Nam ~ 3.2%
    "market_return": 0.125,        # Tỷ suất sinh lời kỳ vọng VN-Index ~ 12.5%
    "equity_risk_premium": 0.093,  # Phần bù rủi ro vốn CP (ERP = Rm - Rf) ~ 9.3%
    "terminal_growth_rate": 0.035, # Tăng trưởng dài hạn vĩnh viễn ~ 3.5% (phù hợp lạm phát mục tiêu)
    "corporate_tax_rate": 0.20,    # Thuế thu nhập doanh nghiệp phổ thông 20%
    "refinancing_rate": 0.045,     # Lãi suất tái cấp vốn NHNN 4.5%
    "discount_rate": 0.030,        # Lãi suất tái chiết khấu NHNN 3.0%
    "gdp_growth_target": 0.070,    # Mục tiêu tăng trưởng GDP 7.0%
    "cpi_inflation_target": 0.040  # Mục tiêu kiểm soát lạm phát dưới 4.0%
}

# Trọng số và Tiêu chí Đánh giá Quant Multi-Factor Scorecard (Tổng 100 điểm)
SCORECARD_WEIGHTS = {
    "growth": 0.20,           # 20 điểm: Tăng trưởng doanh thu, LNST, CAGR
    "profitability": 0.25,    # 25 điểm: ROE, ROA, Biên lãi gộp/ròng, DuPont
    "financial_health": 0.20, # 20 điểm: Đòn bẩy D/E, Nợ ròng/EBITDA, Khả năng trả lãi, Dòng tiền OCF
    "valuation": 0.20,        # 20 điểm: P/E, P/B so với quá khứ và ngành, Biên an toàn DCF
    "technical": 0.15         # 15 điểm: Xu hướng MA, RSI, MACD, Động lượng thanh khoản
}

# Thang phân loại Khuyến nghị đầu tư
RATING_SCALE = [
    {"min_score": 80, "max_score": 100, "rating": "MUA MẠNH (STRONG BUY)", "action": "Tích cực giải ngân tại các nhịp rung lắc, tỷ trọng danh mục cao"},
    {"min_score": 65, "max_score": 79.9, "rating": "MUA / TÍCH LŨY (ACCUMULATE)", "action": "Giải ngân từng phần tại các vùng hỗ trợ kỹ thuật"},
    {"min_score": 50, "max_score": 64.9, "rating": "NẮM GIỮ (HOLD)", "action": "Duy trì vị thế hiện tại, quan sát thêm tín hiệu xác nhận"},
    {"min_score": 35, "max_score": 49.9, "rating": "THEO DÕI / TRUNG LẬP (NEUTRAL)", "action": "Tạm dừng mua mới, chờ đợi định giá chiết khấu sâu hơn"},
    {"min_score": 0,  "max_score": 34.9, "rating": "GIẢM TỶ TRỌNG (REDUCE)", "action": "Cơ cấu danh mục, ưu tiên quản trị rủi ro bảo toàn vốn"}
]

# Cấu hình Báo cáo PDF
PDF_CONFIG = {
    "organization": "VIETNAM QUANTITATIVE EQUITY RESEARCH",
    "system_name": "Antigravity Investment Intelligence Platform",
    "primary_color": "#1A365D",    # Deep Navy
    "secondary_color": "#2B6CB0",  # Slate Blue
    "accent_color": "#2E7D32",     # Forest Green
    "warning_color": "#C53030",    # Deep Red
    "neutral_bg": "#F7FAFC",       # Soft Grey Background
    "text_dark": "#2D3748",
    "text_light": "#FFFFFF",
    "font_family": "Arial"
}
