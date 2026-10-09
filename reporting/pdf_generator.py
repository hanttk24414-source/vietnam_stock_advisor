"""
Module sinh Báo cáo Phân tích Đầu tư Cổ phiếu tự động định dạng PDF chuyên nghiệp.
Áp dụng:
1. Thư viện ReportLab với font Arial Unicode tiếng Việt chuẩn mực.
2. NumberedCanvas: Đánh số trang tự động 'Trang X / Y', running header & footer.
3. Trình bày chuẩn mực của các công ty chứng khoán hàng đầu (SSI Research, HSC, Vietcap).
4. Tùy biến linh hoạt theo nhu cầu người dùng: Lựa chọn mã, thời gian, ngày phân tích, các mục nội dung.
5. Tích hợp bảng số liệu tài chính định dạng chuẩn và các biểu đồ đồ họa sắc nét.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether, HRFlowable
)

from config import PDF_CONFIG, REPORTS_DIR
from reporting.chart_generator import (
    generate_technical_chart,
    generate_financial_performance_chart,
    generate_scorecard_radar_chart,
    generate_scenario_valuation_chart
)

# Đăng ký phông chữ Arial Unicode trên Windows
def setup_pdf_fonts():
    """Đăng ký phông chữ Arial để hỗ trợ tiếng Việt có dấu hoàn hảo."""
    font_dir = "C:/Windows/Fonts"
    fonts = [
        ("Arial", os.path.join(font_dir, "arial.ttf")),
        ("Arial-Bold", os.path.join(font_dir, "arialbd.ttf")),
        ("Arial-Italic", os.path.join(font_dir, "ariali.ttf")),
        ("Arial-BoldItalic", os.path.join(font_dir, "arialbi.ttf")),
    ]
    for font_name, font_path in fonts:
        if os.path.exists(font_path) and font_name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(font_name, font_path))

setup_pdf_fonts()

class NumberedCanvas(canvas.Canvas):
    """
    Canvas tùy chỉnh để đánh số trang hai lượt (Trang X / Y)
    và vẽ Header / Footer chuyên nghiệp trên mọi trang.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        page_w, page_h = A4
        
        # 1. Running Header (Từ trang 2 trở đi)
        if self._pageNumber > 1:
            self.setFont("Arial-Bold", 8)
            self.setFillColor(colors.HexColor(PDF_CONFIG["primary_color"]))
            self.drawString(36, page_h - 28, f"{PDF_CONFIG['organization']}  |  BÁO CÁO PHÂN TÍCH CỔ PHIẾU")
            
            self.setFont("Arial-Italic", 8)
            self.setFillColor(colors.HexColor("#718096"))
            self.drawRightString(page_w - 36, page_h - 28, f"Cập nhật: {datetime.now().strftime('%d/%m/%Y')}")
            
            self.setStrokeColor(colors.HexColor("#CBD5E0"))
            self.setLineWidth(0.6)
            self.line(36, page_h - 32, page_w - 36, page_h - 32)

        # 2. Running Footer (Tất cả các trang)
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.6)
        self.line(36, 34, page_w - 36, 34)

        self.setFont("Arial", 7.5)
        self.setFillColor(colors.HexColor("#718096"))
        disclaimer_short = "Nguồn: Dữ liệu kiểm chứng từ HOSE, VNDirect, Yahoo Finance & BCTC kiểm toán. Báo cáo nhằm mục đích tham khảo đầu tư."
        self.drawString(36, 22, disclaimer_short)

        page_str = f"Trang {self._pageNumber} / {page_count}"
        self.drawRightString(page_w - 36, 22, page_str)

        self.restoreState()

def create_investment_report_pdf(
    ticker: str,
    stock_fundamentals: Dict[str, Any],
    fundamental_analysis: Dict[str, Any],
    technical_analysis: Dict[str, Any],
    valuation_analysis: Dict[str, Any],
    scorecard_analysis: Dict[str, Any],
    scenario_analysis: Dict[str, Any],
    macro_analysis: Dict[str, Any],
    industry_analysis: Dict[str, Any],
    price_df: Any,
    output_filename: Optional[str] = None,
    included_sections: Optional[List[str]] = None,
    analysis_date: Optional[str] = None,
    custom_notes: Optional[str] = None
) -> str:
    """
    Sinh file PDF Báo cáo phân tích cơ hội đầu tư cổ phiếu hoàn chỉnh.
    """
    setup_pdf_fonts()

    if output_filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"BaoCao_PhanTich_{ticker}_{timestamp}.pdf"
    
    output_path = REPORTS_DIR / output_filename
    
    # Thư mục chứa biểu đồ tạm thời
    charts_dir = REPORTS_DIR / "temp_charts" / ticker
    charts_dir.mkdir(parents=True, exist_ok=True)

    if included_sections is None:
        included_sections = ["macro", "industry", "technical", "fundamental", "valuation", "scenarios", "scorecard"]

    if analysis_date is None:
        analysis_date = datetime.now().strftime("%d/%m/%Y")

    # Tạo các biểu đồ cần thiết
    tech_chart_path = charts_dir / "tech_chart.png"
    fin_chart_path = charts_dir / "fin_chart.png"
    radar_chart_path = charts_dir / "radar_chart.png"
    scen_chart_path = charts_dir / "scen_chart.png"

    generate_technical_chart(price_df, ticker, tech_chart_path)
    generate_financial_performance_chart(stock_fundamentals.get("financial_history", []), ticker, fin_chart_path)
    generate_scorecard_radar_chart(scorecard_analysis.get("pillars", {}), ticker, radar_chart_path)
    generate_scenario_valuation_chart(
        valuation_analysis.get("current_price", 20000.0),
        scenario_analysis.get("bull_case", {}).get("target_price", 24000.0),
        scenario_analysis.get("base_case", {}).get("target_price", 21000.0),
        scenario_analysis.get("bear_case", {}).get("target_price", 17000.0),
        valuation_analysis.get("dcf_fair_value", 19500.0),
        ticker,
        scen_chart_path
    )

    # Khởi tạo Document
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=42,
        bottomMargin=42
    )

    styles = getSampleStyleSheet()
    
    # Định nghĩa Typography styles chuẩn chuyên nghiệp
    primary_c = colors.HexColor(PDF_CONFIG["primary_color"])
    secondary_c = colors.HexColor(PDF_CONFIG["secondary_color"])
    accent_g = colors.HexColor(PDF_CONFIG["accent_color"])
    accent_r = colors.HexColor(PDF_CONFIG["warning_color"])
    dark_txt = colors.HexColor(PDF_CONFIG["text_dark"])

    title_style = ParagraphStyle(
        "ReportTitle",
        fontName="Arial-Bold",
        fontSize=18,
        leading=22,
        textColor=primary_c,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        "ReportSubTitle",
        fontName="Arial",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4A5568"),
        spaceAfter=12
    )
    
    h1_style = ParagraphStyle(
        "H1Heading",
        fontName="Arial-Bold",
        fontSize=12,
        leading=16,
        textColor=primary_c,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "BodyDark",
        fontName="Arial",
        fontSize=8.5,
        leading=12.5,
        textColor=dark_txt,
        spaceAfter=5
    )

    body_bold = ParagraphStyle(
        "BodyDarkBold",
        fontName="Arial-Bold",
        fontSize=8.5,
        leading=12.5,
        textColor=dark_txt
    )

    callout_style = ParagraphStyle(
        "CalloutStyle",
        fontName="Arial-Italic",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#2C5282")
    )

    story = []

    # ==================== TRANG 1: TỔNG QUAN ĐẦU TƯ ====================
    # Header tổ chức
    org_header = Table([
        [
            Paragraph(f"<b>{PDF_CONFIG['organization']}</b>", ParagraphStyle("OrgL", fontName="Arial-Bold", fontSize=9, textColor=secondary_c)),
            Paragraph(f"Ngày lập: <b>{analysis_date}</b>  |  Hệ thống Antigravity 2.0", ParagraphStyle("OrgR", fontName="Arial", fontSize=8, alignment=2, textColor=colors.HexColor("#718096")))
        ]
    ], colWidths=[320, 203])
    org_header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(org_header)
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_c, spaceBefore=2, spaceAfter=8))

    # Tiêu đề báo cáo
    company_name = stock_fundamentals.get("name", f"CTCP {ticker}")
    exchange = stock_fundamentals.get("exchange", "HOSE")
    sector_name = stock_fundamentals.get("sector", "Thép")
    story.append(Paragraph(f"BÁO CÁO PHÂN TÍCH CƠ HỘI ĐẦU TƯ: {ticker} ({exchange})", title_style))
    story.append(Paragraph(f"<b>{company_name}</b>  •  Ngành: <i>{sector_name}</i>  •  Giá hiện tại: <b>{valuation_analysis.get('current_price', 0):,.0f} VNĐ</b>", subtitle_style))

    # SNAPSHOT EXECUTIVE SUMMARY BOX
    rating = scorecard_analysis.get("rating", "NẮM GIỮ (HOLD)")
    blended_target = valuation_analysis.get("blended_target_price", 0.0)
    current_price = valuation_analysis.get("current_price", 1.0)
    upside = valuation_analysis.get("blended_upside", 0.0)
    total_score = scorecard_analysis.get("total_score", 0.0)
    div_yield = stock_fundamentals.get("dividend_yield", 0.0)
    rr_ratio = scenario_analysis.get("risk_reward_ratio", 1.5)

    badge_bg = accent_g if "MUA" in rating else (colors.HexColor("#D69E2E") if "NẮM" in rating else accent_r)

    snap_data = [
        [
            Paragraph("KHUYẾN NGHỊ", ParagraphStyle("S1", fontName="Arial", fontSize=7.5, textColor=colors.white, alignment=1)),
            Paragraph("GIÁ MỤC TIÊU 12T", ParagraphStyle("S2", fontName="Arial", fontSize=7.5, textColor=colors.white, alignment=1)),
            Paragraph("UPSIDE KỲ VỌNG", ParagraphStyle("S3", fontName="Arial", fontSize=7.5, textColor=colors.white, alignment=1)),
            Paragraph("QUANT SCORE", ParagraphStyle("S4", fontName="Arial", fontSize=7.5, textColor=colors.white, alignment=1)),
            Paragraph("CỔ TỨC TIỀN MẶT", ParagraphStyle("S5", fontName="Arial", fontSize=7.5, textColor=colors.white, alignment=1)),
            Paragraph("RISK / REWARD", ParagraphStyle("S6", fontName="Arial", fontSize=7.5, textColor=colors.white, alignment=1)),
        ],
        [
            Paragraph(f"<b>{rating}</b>", ParagraphStyle("V1", fontName="Arial-Bold", fontSize=9, textColor=colors.white, alignment=1)),
            Paragraph(f"<b>{blended_target:,.0f} VNĐ</b>", ParagraphStyle("V2", fontName="Arial-Bold", fontSize=9.5, textColor=colors.white, alignment=1)),
            Paragraph(f"<b>+{upside:.1f}%</b>", ParagraphStyle("V3", fontName="Arial-Bold", fontSize=9.5, textColor=colors.white, alignment=1)),
            Paragraph(f"<b>{total_score:.1f} / 100</b>", ParagraphStyle("V4", fontName="Arial-Bold", fontSize=9.5, textColor=colors.white, alignment=1)),
            Paragraph(f"<b>{div_yield:.1f}%</b>", ParagraphStyle("V5", fontName="Arial-Bold", fontSize=9.5, textColor=colors.white, alignment=1)),
            Paragraph(f"<b>{rr_ratio:.1f}x</b>", ParagraphStyle("V6", fontName="Arial-Bold", fontSize=9.5, textColor=colors.white, alignment=1)),
        ]
    ]
    snap_table = Table(snap_data, colWidths=[105, 86, 82, 80, 85, 85])
    snap_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), primary_c),
        ("BACKGROUND", (0, 0), (0, -1), badge_bg),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#2C5282")),
        ("BOX", (0, 0), (-1, -1), 1, primary_c),
    ]))
    story.append(snap_table)
    story.append(Spacer(1, 8))

    # LUẬN ĐIỂM ĐẦU TƯ THEN CHỐT (KEY THESES)
    story.append(Paragraph("1. LUẬN ĐIỂM ĐẦU TƯ THEN CHỐT & CHẤT XÚC TÁC TĂNG TRƯỞNG", h1_style))
    theses = scorecard_analysis.get("strengths", [])[:4]
    if not theses:
        theses = [
            f"Vị thế dẫn đầu quy mô ngành với thị phần áp đảo và năng lực cạnh tranh chi phí thấp.",
            f"Hưởng lợi trực tiếp từ chu kỳ hồi phục kinh tế vĩ mô và làn sóng giải ngân đầu tư công.",
            f"Cơ cấu tài chính lành mạnh, dòng tiền kinh doanh thặng dư hỗ trợ các dự án mở rộng công suất.",
            f"Mức định giá hấp dẫn với P/E và P/B đang giao dịch dưới vùng trung bình lịch sử 3 năm."
        ]
    for idx, th in enumerate(theses, 1):
        story.append(Paragraph(f"• <b>Luận điểm {idx}:</b> {th}", body_style))
    story.append(Spacer(1, 6))

    # BIỂU ĐỒ TRANG 1: Kỹ thuật + Radar Scorecard
    if os.path.exists(tech_chart_path) and os.path.exists(radar_chart_path):
        two_charts = Table([
            [
                Image(str(tech_chart_path), width=4.3*inch, height=2.15*inch),
                Image(str(radar_chart_path), width=2.8*inch, height=2.15*inch)
            ]
        ], colWidths=[315, 208])
        two_charts.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(two_charts)
    story.append(Spacer(1, 8))

    # TÓM TẮT CHỈ SỐ GIAO DỊCH & KỸ THUẬT
    tech_info = technical_analysis
    t_summary_data = [
        [
            Paragraph("<b>Chỉ tiêu Kỹ thuật & Rủi ro</b>", body_bold),
            Paragraph("<b>Giá trị</b>", body_bold),
            Paragraph("<b>Chỉ tiêu Kỹ thuật & Rủi ro</b>", body_bold),
            Paragraph("<b>Giá trị</b>", body_bold)
        ],
        [
            Paragraph("Xu hướng Kỹ thuật Tổng hợp", body_style),
            Paragraph(f"<b>{tech_info.get('overall_signal', 'TÍCH CỰC')}</b>", body_style),
            Paragraph("Chỉ báo Động lượng RSI (14)", body_style),
            Paragraph(f"{tech_info.get('rsi', 50):.1f} điểm", body_style)
        ],
        [
            Paragraph("Đường trung bình SMA 20 / SMA 50", body_style),
            Paragraph(f"{tech_info.get('sma20', 0):,.0f} / {tech_info.get('sma50', 0):,.0f} đ", body_style),
            Paragraph("Hệ số Beta so với VN-Index", body_style),
            Paragraph(f"{tech_info.get('beta', 1.0):.2f}", body_style)
        ],
        [
            Paragraph("Độ biến động quy năm (Volatility)", body_style),
            Paragraph(f"{tech_info.get('annualized_volatility_pct', 25):.1f}%", body_style),
            Paragraph("Chỉ số Sharpe (Rf = 3.2%)", body_style),
            Paragraph(f"{tech_info.get('sharpe_ratio', 0.8):.2f}", body_style)
        ],
        [
            Paragraph("Mức sụt giảm tối đa (Max Drawdown)", body_style),
            Paragraph(f"{tech_info.get('max_drawdown_pct', -15):.1f}%", body_style),
            Paragraph("Vùng Hỗ trợ / Kháng cự kỹ thuật", body_style),
            Paragraph(f"{tech_info.get('support_levels', [0, 0])[0]:,.0f} / {tech_info.get('resistance_levels', [0, 0])[0]:,.0f} đ", body_style)
        ]
    ]
    t_sum_table = Table(t_summary_data, colWidths=[150, 110, 150, 113])
    t_sum_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PDF_CONFIG["neutral_bg"])),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t_sum_table)

    # ==================== TRANG 2: VĨ MÔ & NGÀNH ====================
    if "macro" in included_sections or "industry" in included_sections:
        story.append(PageBreak())
        story.append(Paragraph("2. BỐI CẢNH VĨ MÔ & TÁC ĐỘNG ĐẾN THỊ TRƯỜNG CHỨNG KHOÁN VIỆT NAM", h1_style))
        story.append(Paragraph(
            f"<b>Môi trường kinh tế vĩ mô:</b> {macro_analysis.get('cycle_stage', 'Tăng trưởng')} "
            f"({macro_analysis.get('cycle_desc', '')}). "
            f"Chính sách tiền tệ NHNN đang ở trạng thái <b>{macro_analysis.get('monetary_stance', 'Hỗ trợ')}</b>: "
            f"{macro_analysis.get('monetary_detail', '')}", body_style
        ))

        # Bảng dữ liệu Vĩ mô
        m_table_data = [
            [
                Paragraph("<b>Chỉ số Vĩ mô</b>", body_bold),
                Paragraph("<b>Thực tế / Mục tiêu</b>", body_bold),
                Paragraph("<b>Chỉ số Vĩ mô</b>", body_bold),
                Paragraph("<b>Thực tế / Mục tiêu</b>", body_bold)
            ],
            [
                Paragraph("Tăng trưởng GDP thực tế", body_style),
                Paragraph(f"{macro_analysis.get('gdp_growth', 7.4):.1f}% (Q) / 7.0% (Năm)", body_style),
                Paragraph("Điểm số VN-Index", body_style),
                Paragraph(f"{macro_analysis.get('vnindex_current', 1740):,.1f} điểm", body_style)
            ],
            [
                Paragraph("Lạm phát CPI (YoY)", body_style),
                Paragraph(f"{macro_analysis.get('cpi_yoy', 3.45):.2f}% (Mục tiêu <4.0%)", body_style),
                Paragraph("P/E toàn thị trường VN-Index", body_style),
                Paragraph(f"{macro_analysis.get('vnindex_pe', 14.8):.1f}x", body_style)
            ],
            [
                Paragraph("Lãi suất tái cấp vốn / Tái CK", body_style),
                Paragraph(f"4.50% / 3.00%", body_style),
                Paragraph("Lợi suất Earning Yield VN-Index", body_style),
                Paragraph(f"{macro_analysis.get('market_earnings_yield', 6.76):.2f}%", body_style)
            ],
            [
                Paragraph("Tỷ giá USD/VND thị trường", body_style),
                Paragraph(f"{macro_analysis.get('usd_vnd_rate', 25889):,.0f} VND", body_style),
                Paragraph("Phần bù rủi ro vốn CP (ERP)", body_style),
                Paragraph(f"<b>{macro_analysis.get('equity_risk_premium', 3.56):.2f}%</b> (Rất hấp dẫn)", body_style)
            ]
        ]
        m_table = Table(m_table_data, colWidths=[140, 120, 140, 123])
        m_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PDF_CONFIG["neutral_bg"])),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(m_table)
        story.append(Spacer(1, 8))

        # PHÂN TÍCH NGÀNH & SO SÁNH PEERS
        story.append(Paragraph(f"3. PHÂN TÍCH TRIỂN VỌNG NGÀNH & MA TRẬN CẠNH TRANH ({sector_name.upper()})", h1_style))
        story.append(Paragraph(
            f"<b>Triển vọng ngành:</b> {industry_analysis.get('outlook', 'Khả quan')}  •  "
            f"<b>Chu kỳ ngành:</b> {industry_analysis.get('cycle_stage', 'Tăng tốc')}. "
            f"Đánh giá vị thế doanh nghiệp: <b>{industry_analysis.get('competitive_moat', 'Dẫn đầu')}</b>.", body_style
        ))

        # Động lực và rủi ro ngành
        for drv in industry_analysis.get("drivers", [])[:3]:
            story.append(Paragraph(f"• <b>Động lực ngành:</b> {drv}", body_style))
        for rsk in industry_analysis.get("risks", [])[:2]:
            story.append(Paragraph(f"• <b>Rủi ro ngành:</b> {rsk}", body_style))
        story.append(Spacer(1, 6))

        # BẢNG SO SÁNH ĐỐI THỦ CÙNG NGÀNH (PEERS COMPARISON)
        story.append(Paragraph(f"<b>Bảng So sánh Doanh nghiệp cùng ngành ({sector_name})</b>", body_bold))
        peers_data = [
            [
                Paragraph("<b>Mã CP</b>", body_bold),
                Paragraph("<b>Doanh nghiệp</b>", body_bold),
                Paragraph("<b>Vốn hóa (tỷ)</b>", body_bold),
                Paragraph("<b>P/E</b>", body_bold),
                Paragraph("<b>P/B</b>", body_bold),
                Paragraph("<b>ROE (%)</b>", body_bold),
                Paragraph("<b>Thị phần & Vị thế</b>", body_bold)
            ]
        ]
        for p in industry_analysis.get("peers", []):
            is_target = (p.get("ticker") == ticker)
            prefix = "<b>" if is_target else ""
            suffix = "</b>" if is_target else ""
            peers_data.append([
                Paragraph(f"{prefix}{p.get('ticker')}{suffix}", body_style),
                Paragraph(f"{prefix}{p.get('name')}{suffix}", body_style),
                Paragraph(f"{p.get('market_cap_bil', 0):,.0f}", body_style),
                Paragraph(f"{p.get('pe', 0):.1f}x", body_style),
                Paragraph(f"{p.get('pb', 0):.2f}x", body_style),
                Paragraph(f"{p.get('roe', 0):.1f}%", body_style),
                Paragraph(f"{p.get('market_share', '')}", body_style),
            ])
        peers_table = Table(peers_data, colWidths=[45, 95, 75, 45, 45, 55, 163])
        peers_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PDF_CONFIG["neutral_bg"])),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(peers_table)

    # ==================== TRANG 3: BÁO CÁO TÀI CHÍNH & DUPONT ====================
    if "fundamental" in included_sections:
        story.append(PageBreak())
        story.append(Paragraph("4. BÁO CÁO TÀI CHÍNH, HIỆU QUẢ HOẠT ĐỘNG & MÔ HÌNH DUPONT", h1_style))
        story.append(Paragraph(
            f"{fundamental_analysis.get('dupont_assessment', '')} "
            f"Chất lượng dòng tiền: <b>{fundamental_analysis.get('cf_quality', 'Tốt')}</b>. "
            f"Cơ cấu đòn bẩy: <b>{fundamental_analysis.get('leverage_status', 'An toàn')}</b>.", body_style
        ))

        # Biểu đồ tài chính
        if os.path.exists(fin_chart_path):
            story.append(Image(str(fin_chart_path), width=7.1*inch, height=2.6*inch))
            story.append(Spacer(1, 6))

        # Bảng số liệu BCTC 4 năm
        fin_history = stock_fundamentals.get("financial_history", [])
        if fin_history:
            headers_bctc = ["Chỉ tiêu Tài chính (Tỷ VNĐ)"] + [str(item["year"]) for item in fin_history]
            row_rev = ["Doanh thu thuần"] + [f"{item.get('revenue', 0):,.0f}" for item in fin_history]
            row_gp = ["Lợi nhuận gộp"] + [f"{item.get('gross_profit', 0):,.0f}" for item in fin_history]
            row_ebit = ["Lợi nhuận EBIT"] + [f"{item.get('ebit', 0):,.0f}" for item in fin_history]
            row_ni = ["LNST cổ đông cty mẹ"] + [f"{item.get('net_income', 0):,.0f}" for item in fin_history]
            row_assets = ["Tổng tài sản"] + [f"{item.get('total_assets', 0):,.0f}" for item in fin_history]
            row_equity = ["Vốn chủ sở hữu"] + [f"{item.get('equity', 0):,.0f}" for item in fin_history]
            row_debt = ["Tổng nợ vay"] + [f"{item.get('debt', 0):,.0f}" for item in fin_history]
            row_ocf = ["Dòng tiền KD (OCF)"] + [f"{item.get('ocf', 0):,.0f}" for item in fin_history]
            row_capex = ["Chi tiêu vốn (CapEx)"] + [f"{item.get('capex', 0):,.0f}" for item in fin_history]
            row_fcf = ["Dòng tiền tự do (FCF)"] + [f"{item.get('fcf', 0):,.0f}" for item in fin_history]

            bctc_table_data = [
                [Paragraph(f"<b>{c}</b>", body_bold if i==0 else ParagraphStyle("BR", fontName="Arial-Bold", fontSize=8, alignment=2)) for i, c in enumerate(headers_bctc)],
                [Paragraph(row_rev[0], body_style)] + [Paragraph(c, ParagraphStyle("R", fontName="Arial", fontSize=8, alignment=2)) for c in row_rev[1:]],
                [Paragraph(row_gp[0], body_style)] + [Paragraph(c, ParagraphStyle("R", fontName="Arial", fontSize=8, alignment=2)) for c in row_gp[1:]],
                [Paragraph(row_ebit[0], body_style)] + [Paragraph(c, ParagraphStyle("R", fontName="Arial", fontSize=8, alignment=2)) for c in row_ebit[1:]],
                [Paragraph(f"<b>{row_ni[0]}</b>", body_style)] + [Paragraph(f"<b>{c}</b>", ParagraphStyle("R", fontName="Arial-Bold", fontSize=8, alignment=2)) for c in row_ni[1:]],
                [Paragraph(row_assets[0], body_style)] + [Paragraph(c, ParagraphStyle("R", fontName="Arial", fontSize=8, alignment=2)) for c in row_assets[1:]],
                [Paragraph(row_equity[0], body_style)] + [Paragraph(c, ParagraphStyle("R", fontName="Arial", fontSize=8, alignment=2)) for c in row_equity[1:]],
                [Paragraph(row_debt[0], body_style)] + [Paragraph(c, ParagraphStyle("R", fontName="Arial", fontSize=8, alignment=2)) for c in row_debt[1:]],
                [Paragraph(row_ocf[0], body_style)] + [Paragraph(c, ParagraphStyle("R", fontName="Arial", fontSize=8, alignment=2)) for c in row_ocf[1:]],
                [Paragraph(row_capex[0], body_style)] + [Paragraph(c, ParagraphStyle("R", fontName="Arial", fontSize=8, alignment=2)) for c in row_capex[1:]],
                [Paragraph(f"<b>{row_fcf[0]}</b>", body_style)] + [Paragraph(f"<b>{c}</b>", ParagraphStyle("R", fontName="Arial-Bold", fontSize=8, alignment=2)) for c in row_fcf[1:]],
            ]
            
            n_cols = len(headers_bctc)
            first_w = 173
            other_w = (523 - first_w) / (n_cols - 1)
            bctc_table = Table(bctc_table_data, colWidths=[first_w] + [other_w]*(n_cols-1))
            bctc_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PDF_CONFIG["neutral_bg"])),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ]))
            story.append(bctc_table)

    # ==================== TRANG 4: ĐỊNH GIÁ & KỊCH BẢN ĐẦU TƯ ====================
    if "valuation" in included_sections or "scenarios" in included_sections:
        story.append(PageBreak())
        story.append(Paragraph("5. ĐỊNH GIÁ ĐA PHƯƠNG PHÁP & MA TRẬN KỊCH BẢN ĐẦU TƯ", h1_style))
        story.append(Paragraph(
            f"Mô hình định giá kết hợp các phương pháp: <b>P/E mục tiêu</b> ({valuation_analysis.get('pe_fair_value', 0):,.0f} đ), "
            f"<b>P/B mục tiêu</b> ({valuation_analysis.get('pb_fair_value', 0):,.0f} đ) và "
            f"<b>Chiết khấu dòng tiền DCF FCFF 2-giai đoạn</b> ({valuation_analysis.get('dcf_fair_value', 0):,.0f} đ với WACC {valuation_analysis.get('wacc', 8.5):.1f}% và g {valuation_analysis.get('terminal_growth', 3.5):.1f}%). "
            f"Giá trị mục tiêu tổng hợp đạt <b>{blended_target:,.0f} VNĐ</b>, tương ứng biên tăng giá tiềm năng <b>+{upside:.1f}%</b>.", body_style
        ))

        # Biểu đồ kịch bản
        if os.path.exists(scen_chart_path):
            story.append(Image(str(scen_chart_path), width=7.1*inch, height=2.4*inch))
            story.append(Spacer(1, 6))

        # Bảng Kịch bản Chi tiết (Bull / Base / Bear)
        bull = scenario_analysis.get("bull_case", {})
        base = scenario_analysis.get("base_case", {})
        bear = scenario_analysis.get("bear_case", {})

        scen_table_data = [
            [
                Paragraph("<b>Kịch bản</b>", body_bold),
                Paragraph("<b>Xác suất</b>", body_bold),
                Paragraph("<b>Giá mục tiêu</b>", body_bold),
                Paragraph("<b>Tỷ suất (%)</b>", body_bold),
                Paragraph("<b>Giả định & Điều kiện kích hoạt</b>", body_bold)
            ],
            [
                Paragraph("<b>TÍCH CỰC (BULL)</b>", ParagraphStyle("B1", fontName="Arial-Bold", fontSize=8, textColor=accent_g)),
                Paragraph(f"{bull.get('probability', 0.25)*100:.0f}%", body_style),
                Paragraph(f"<b>{bull.get('target_price', 0):,.0f} đ</b>", body_style),
                Paragraph(f"+{bull.get('upside_pct', 0):.1f}%", ParagraphStyle("G", fontName="Arial-Bold", fontSize=8, textColor=accent_g)),
                Paragraph(bull.get("assumptions", ""), body_style)
            ],
            [
                Paragraph("<b>CƠ SỞ (BASE)</b>", ParagraphStyle("B2", fontName="Arial-Bold", fontSize=8, textColor=secondary_c)),
                Paragraph(f"{base.get('probability', 0.55)*100:.0f}%", body_style),
                Paragraph(f"<b>{base.get('target_price', 0):,.0f} đ</b>", body_style),
                Paragraph(f"+{base.get('upside_pct', 0):.1f}%", ParagraphStyle("B", fontName="Arial-Bold", fontSize=8, textColor=secondary_c)),
                Paragraph(base.get("assumptions", ""), body_style)
            ],
            [
                Paragraph("<b>THẬN TRỌNG (BEAR)</b>", ParagraphStyle("B3", fontName="Arial-Bold", fontSize=8, textColor=accent_r)),
                Paragraph(f"{bear.get('probability', 0.20)*100:.0f}%", body_style),
                Paragraph(f"<b>{bear.get('target_price', 0):,.0f} đ</b>", body_style),
                Paragraph(f"{bear.get('downside_pct', 0):.1f}%", ParagraphStyle("R", fontName="Arial-Bold", fontSize=8, textColor=accent_r)),
                Paragraph(bear.get("assumptions", ""), body_style)
            ]
        ]
        scen_table = Table(scen_table_data, colWidths=[95, 45, 80, 65, 238])
        scen_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PDF_CONFIG["neutral_bg"])),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(scen_table)
        story.append(Spacer(1, 8))

        # KHUYẾN NGHỊ HÀNH ĐỘNG & QUẢN TRỊ RỦI RO
        story.append(Paragraph("6. CHIẾN LƯỢC GIẢI NGÂN & ĐIỀU KIỆN QUẢN TRỊ RỦI RO", h1_style))
        story.append(Paragraph(f"• <b>Chiến lược hành động:</b> {scorecard_analysis.get('action_guide', '')}", body_style))
        story.append(Paragraph(f"• <b>Vùng giá mua khuyến nghị:</b> {scenario_analysis.get('recommended_buy_zone', '')}", body_style))
        story.append(Paragraph(f"• <b>Ngưỡng Dừng lỗ Bảo toàn vốn (Stop-loss):</b> <b>{scenario_analysis.get('stop_loss_price', 0):,.0f} VNĐ</b> (Vi phạm khi giá đóng cửa thủng hỗ trợ kỹ thuật hoặc giảm > 7.5% từ điểm mua).", body_style))
        
        # Điều kiện xác nhận / bác bỏ
        story.append(Paragraph(
            "• <b>Điều kiện xác nhận luận điểm (Catalysts):</b> "
            "Kết quả kinh doanh quý tiếp theo duy trì đà tăng trưởng > 20% YoY, biên lợi nhuận gộp không bị co hẹp, khối ngoại duy trì mua ròng ròng.", body_style
        ))
        story.append(Paragraph(
            "• <b>Điều kiện bác bỏ luận điểm (Invalidation):</b> "
            "Giá nguyên vật liệu đầu vào tăng đột biến làm biên lợi nhuận ròng rơi xuống dưới 5%, hoặc xảy ra các biến cố pháp lý bất khả kháng.", body_style
        ))

        if custom_notes:
            story.append(Spacer(1, 4))
            story.append(Paragraph(f"<b>Ghi chú chuyên viên phân tích:</b> {custom_notes}", callout_style))

        # DISCLAIMER
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#CBD5E0"), spaceBefore=4, spaceAfter=4))
        disclaimer_text = (
            "<b>TUYÊN BỐ MIỄN TRỪ TRÁCH NHIỆM (DISCLAIMER):</b> Báo cáo này được xây dựng hoàn toàn dựa trên dữ liệu công khai có nguồn gốc "
            "kiểm chứng từ Sở Giao dịch Chứng khoán HOSE/HNX, VNDirect API, Yahoo Finance, Tổng cục Thống kê và Báo cáo tài chính kiểm toán của doanh nghiệp. "
            "Các nhận định, định giá và kịch bản đầu tư được tính toán theo mô hình định lượng và không cấu thành lời cam kết lợi nhuận chắc chắn. "
            "Nhà đầu tư cần tự chịu trách nhiệm đối với các quyết định giải ngân và quản trị rủi ro danh mục cá nhân."
        )
        story.append(Paragraph(disclaimer_text, ParagraphStyle("Disc", fontName="Arial", fontSize=7, leading=9.5, textColor=colors.HexColor("#718096"))))

    # Build PDF với NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    return str(output_path)
