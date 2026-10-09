"""
Ứng dụng Web Phân tích Cơ hội Đầu tư Cổ phiếu Việt Nam
Vietnam Stock Investment Analysis & Automated Reporting Platform
Sử dụng công nghệ: Streamlit, Plotly, Pandas, ReportLab
"""

import os
from datetime import datetime
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from config import SUPPORTED_TICKERS, MACRO_DEFAULTS, REPORTS_DIR, RATING_SCALE
from data.macro_loader import fetch_macro_indicators, fetch_vnindex_history
from data.industry_loader import get_industry_analysis
from data.stock_loader import fetch_stock_price_history, fetch_stock_fundamentals, clean_ticker, fetch_stock_list, sync_market_price, DataUnavailableError
from analytics.macro_engine import analyze_macro_environment
from analytics.industry_engine import evaluate_industry_and_peers
from analytics.technical_engine import compute_technical_indicators
from analytics.fundamental_engine import analyze_fundamentals
from analytics.valuation_engine import perform_valuation
from analytics.scorecard_engine import calculate_quant_scorecard, build_scenario_matrix
from analytics.recommendation_engine import build_recommendation
from reporting.pdf_generator import create_investment_report_pdf
from data.dnse_loader import dnse_configured

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="Hệ thống Phân tích Cơ hội Đầu tư Cổ phiếu Việt Nam",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS cho giao diện phong cách tổ chức tài chính chuyên nghiệp
st.markdown("""
<style>
    .main-title {
        font-size: 26px;
        font-weight: 800;
        color: #1A365D;
        margin-bottom: 2px;
    }
    .sub-title {
        font-size: 14px;
        color: #4A5568;
        margin-bottom: 15px;
    }
    .metric-card {
        background-color: #F7FAFC;
        border-radius: 8px;
        padding: 12px 16px;
        border-left: 4px solid #2B6CB0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .metric-value {
        font-size: 22px;
        font-weight: 700;
        color: #1A202C;
    }
    .metric-label {
        font-size: 11px;
        font-weight: 600;
        color: #718096;
        text-transform: uppercase;
    }
    .badge-buy {
        background-color: #2E7D32;
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 13px;
        display: inline-block;
    }
    .badge-hold {
        background-color: #D69E2E;
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 13px;
        display: inline-block;
    }
    .badge-reduce {
        background-color: #C53030;
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 13px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR: BỘ ĐIỀU KHIỂN & CẤU HÌNH -----------------
with st.sidebar:
    st.markdown("### ⚙️ BỘ ĐIỀU KHIỂN HỆ THỐNG")
    
    if dnse_configured():
        st.success("Nguồn giá DNSE: đã cấu hình API; sẽ ưu tiên khi truy vấn.")
    else:
        st.info("Chưa cấu hình DNSE: điền DNSE_API_KEY và DNSE_API_SECRET trong .env trên máy.")
    # 1. Chọn mã cổ phiếu
    @st.cache_data(ttl=3600, show_spinner=False)
    def listed_stocks():
        return fetch_stock_list()
    stock_list = listed_stocks()
    ticker_options = sorted(set(stock_list) | set(SUPPORTED_TICKERS))
    selected_ticker = st.selectbox(
        "📌 Chọn mã cổ phiếu phân tích:",
        ticker_options,
        index=ticker_options.index("HPG"),
        format_func=lambda sym: f"{sym} — {stock_list.get(sym, SUPPORTED_TICKERS.get(sym, {})).get('name', sym)}",
        help="Chọn mã cổ phiếu trong danh mục trọng điểm hoặc nhập mã khác bên dưới"
    )
    
    custom_input = st.text_input("Hoặc nhập mã CP khác (ví dụ: TCB, VNM, MBB):", "").strip()
    if custom_input:
        try:
            selected_ticker = clean_ticker(custom_input)
        except ValueError as exc:
            st.error(str(exc))
            st.stop()

    # 2. Chọn khung thời gian
    timeframe = st.selectbox(
        "⏱️ Khoảng thời gian phân tích:",
        ["1 Năm (1Y)", "3 Năm (3Y)", "5 Năm (5Y)"],
        index=0
    )
    days_map = {"1 Năm (1Y)": 365, "3 Năm (3Y)": 1095, "5 Năm (5Y)": 1825}
    days_to_fetch = days_map.get(timeframe, 365)

    # 3. Ngày phân tích
    analysis_date = st.date_input("📅 Ngày phân tích:", datetime.now())

    st.markdown("---")
    st.markdown("### 🎛️ THAM SỐ ĐỊNH GIÁ DCF")
    custom_benchmarks = st.checkbox("Tự nhập giả định P/E, P/B ngành", value=False,
                                   help="Dùng khi ngành chưa có benchmark; số nhập là giả định của bạn.")
    if custom_benchmarks:
        custom_pe = st.number_input("P/E mục tiêu tham chiếu ngành (lần)", min_value=1.0, value=12.0)
        custom_pb = st.number_input("P/B mục tiêu tham chiếu ngành (lần)", min_value=0.1, value=1.5)
    wacc_input = st.slider("Chi phí vốn bình quân WACC (%):", 6.0, 14.0, 8.5, 0.25) / 100.0
    g_input = st.slider("Tăng trưởng dài hạn vĩnh viễn g (%):", 2.0, 5.0, 3.5, 0.25) / 100.0

    st.markdown("---")
    st.markdown("### 📑 TÙY CHỌN MỤC BÁO CÁO PDF")
    inc_macro = st.checkbox("1. Bối cảnh Vĩ mô Việt Nam", value=True)
    inc_industry = st.checkbox("2. Phân tích Ngành & Cạnh tranh", value=True)
    inc_technical = st.checkbox("3. Phân tích Kỹ thuật & Động lượng", value=True)
    inc_fund = st.checkbox("4. Báo cáo Tài chính & DuPont", value=True)
    inc_val = st.checkbox("5. Định giá & Ma trận Kịch bản", value=True)
    inc_score = st.checkbox("6. Bảng điểm Quant Multi-Factor", value=True)
    
    custom_analyst_notes = st.text_area(
        "Ghi chú của chuyên viên phân tích:",
        ""
    )

# ----------------- TẢI & XỬ LÝ DỮ LIỆU ĐA TẦNG -----------------
with st.spinner(f"Đang phân tích cơ hội đầu tư cho mã {selected_ticker}..."):
    # Cache market context independently from the selected ticker.
    @st.cache_data(ttl=900, show_spinner=False)
    def load_macro(days):
        return fetch_macro_indicators(), fetch_vnindex_history(days)
    macro_raw, vnindex_df = load_macro(days_to_fetch)
    macro_analysis = analyze_macro_environment(macro_raw)

    # 2. Dữ liệu Cổ phiếu
    @st.cache_data(ttl=900, show_spinner=False)
    def load_stock(symbol, days):
        frame = fetch_stock_price_history(symbol, days)
        raw = sync_market_price(fetch_stock_fundamentals(symbol), frame)
        return frame, raw
    try:
        price_df, stock_raw = load_stock(selected_ticker, days_to_fetch)
    except (DataUnavailableError, ValueError) as exc:
        st.error(str(exc))
        st.stop()
    st.caption(f"{selected_ticker} · Nguồn giá: {price_df.attrs.get('data_source')} · Phiên cuối: {price_df.attrs.get('price_as_of')} · BCTC: {stock_raw.get('data_source')}")
    if price_df.attrs.get('stale') or price_df.attrs.get('cached'):
        st.warning("Giá từ cache hoặc chưa cập nhật; kiểm tra phiên giao dịch cuối trước khi sử dụng.")
    if stock_raw.get('data_warning'):
        st.warning(stock_raw['data_warning'])
    
    # 3. Động cơ Phân tích
    tech_analysis = compute_technical_indicators(price_df, vnindex_df)
    fund_analysis = analyze_fundamentals(stock_raw)
    sector_code = stock_raw.get("sector_code", "GENERAL")
    ind_analysis = evaluate_industry_and_peers(sector_code, stock_raw)
    if custom_benchmarks:
        ind_analysis.update(benchmark_pe=custom_pe, benchmark_pb=custom_pb,
                            benchmark_source="Giả định do người dùng nhập")
        pe, pb = stock_raw.get('pe', 0), stock_raw.get('pb', 0)
        ind_analysis['pe_discount_pct'] = (1-pe/custom_pe)*100 if pe > 0 else 0
        ind_analysis['pb_discount_pct'] = (1-pb/custom_pb)*100 if pb > 0 else 0
    st.caption(ind_analysis['benchmark_source'])
    st.caption("GDP/CPI/lãi suất và benchmark ngành trong bản này còn có giá trị cấu hình; cần đối chiếu nguồn công bố.")
    
    if not tech_analysis:
        st.warning("Chưa đủ 20 phiên hợp lệ để phân tích kỹ thuật.")
        st.line_chart(price_df['close'])
        st.stop()
    try:
        val_analysis = perform_valuation(stock_raw, fund_analysis, ind_analysis,
            beta=tech_analysis.get("beta", 1.1), custom_wacc=wacc_input, custom_g=g_input)
    except ValueError as exc:
        val_analysis = {"available": False}
        st.warning(str(exc))
    if not fund_analysis.get('available') or fund_analysis.get('missing_fields') or not val_analysis.get('available'):
        recommendation = build_recommendation(selected_ticker, tech_analysis, fund_analysis,
                                               val_analysis, price_status=price_df.attrs)
        st.subheader(f"Phân tích {selected_ticker}")
        st.info(recommendation['rating'])
        st.write(recommendation['action_guide'])
        for fact in recommendation['evidence']:
            st.write(fact)
        st.line_chart(price_df['close'])
        st.write("Điều kiện xác nhận kỹ thuật: " + recommendation['confirmation'])
        st.write("Điều kiện đánh giá lại: " + recommendation['invalidation'])
        for risk in recommendation['risks']:
            st.warning(risk)
        if stock_raw.get('financial_history'):
            st.dataframe(pd.DataFrame(stock_raw['financial_history']), hide_index=True)
        st.caption("Báo cáo đầu tư đầy đủ sẽ khả dụng khi có đủ BCTC, số cổ phiếu lưu hành và cơ sở định giá ngành.")
        st.stop()

    scorecard_analysis = calculate_quant_scorecard(
        fund_analysis,
        tech_analysis,
        val_analysis,
        ind_analysis,
        macro_analysis,
        ticker=selected_ticker, price_status=price_df.attrs
    )
    scenario_analysis = build_scenario_matrix(
        val_analysis["current_price"],
        val_analysis["blended_target_price"],
        fund_analysis,
        tech_analysis
    )

# ----------------- HEADER & EXECUTIVE KPI CARDS -----------------
st.subheader(f"Khuyến nghị cho {selected_ticker}: {scorecard_analysis['rating']}")
st.write(scorecard_analysis['summary'])
st.write(scorecard_analysis['action_guide'])
st.write("Xác nhận: " + scorecard_analysis['confirmation'])
st.write("Đánh giá lại: " + scorecard_analysis['invalidation'])
st.caption(val_analysis['assumptions'])
st.caption(scenario_analysis['assumption_notice'])
st.markdown(f"<div class='main-title'>HỆ THỐNG PHÂN TÍCH CƠ HỘI ĐẦU TƯ: {selected_ticker} ({stock_raw.get('exchange', 'HOSE')})</div>", unsafe_allow_html=True)
st.markdown(f"<div class='sub-title'><b>{stock_raw.get('name', '')}</b>  |  Ngành: <b>{stock_raw.get('sector', '')}</b>  |  Ngày cập nhật: <b>{analysis_date.strftime('%d/%m/%Y')}</b></div>", unsafe_allow_html=True)

# Khối KPI hàng đầu
c1, c2, c3, c4, c5, c6 = st.columns(6)

cur_p = val_analysis.get("current_price", 20000.0)
target_p = val_analysis.get("blended_target_price", 21000.0)
up_pct = val_analysis.get("blended_upside", 5.0)
rating = scorecard_analysis.get("rating", "NẮM GIỮ")
total_score = scorecard_analysis.get("total_score", 70.0)
pe_val = stock_raw.get("pe", 0.0)
pb_val = stock_raw.get("pb", 0.0)
roe_val = fund_analysis.get("roe", 15.0)
div_y = stock_raw.get("dividend_yield", 0.0)

with c1:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>Thị giá Hiện tại</div>
        <div class='metric-value'>{cur_p:,.0f} <span style='font-size:12px;'>đ</span></div>
        <span style='font-size:11px; color:#4A5568;'>Phiên gần nhất</span>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>Giá Mục tiêu 12T</div>
        <div class='metric-value' style='color:#2B6CB0;'>{target_p:,.0f} <span style='font-size:12px;'>đ</span></div>
        <span style='font-size:11px; color:#2E7D32; font-weight:700;'>+{up_pct:.1f}% Upside</span>
    </div>
    """, unsafe_allow_html=True)

with c3:
    badge_cls = "badge-buy" if "MUA" in rating else ("badge-hold" if "NẮM" in rating else "badge-reduce")
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>Khuyến nghị Hệ thống</div>
        <div style='margin-top:4px;'><span class='{badge_cls}'>{rating}</span></div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>Quant Scorecard</div>
        <div class='metric-value' style='color:#6B46C1;'>{total_score:.1f} <span style='font-size:12px;'>/ 100</span></div>
        <span style='font-size:11px; color:#718096;'>Đa nhân tố</span>
    </div>
    """, unsafe_allow_html=True)

with c5:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>Định giá P/E & P/B</div>
        <div class='metric-value'>{pe_val:.1f}x <span style='font-size:14px; color:#718096;'>| {pb_val:.2f}x</span></div>
        <span style='font-size:11px; color:#718096;'>So với ngành {ind_analysis.get('benchmark_pe', 12):.1f}x</span>
    </div>
    """, unsafe_allow_html=True)

with c6:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>ROE & Tỷ suất Cổ tức</div>
        <div class='metric-value' style='color:#2E7D32;'>{roe_val:.1f}% <span style='font-size:14px; color:#718096;'>| {div_y:.1f}%</span></div>
        <span style='font-size:11px; color:#718096;'>Hiệu quả sinh lời</span>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# ----------------- TABS GIAO DIỆN CHUYÊN SÂU -----------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🌐 1. Vĩ mô & TTCK",
    "🏭 2. Ngành & Đối thủ",
    "📈 3. Kỹ thuật & BCTC",
    "🎯 4. Định giá & Scorecard",
    "📄 5. Xuất Báo cáo PDF"
])

# ==================== TAB 1: VĨ MÔ ====================
with tab1:
    st.subheader("🌐 Tổng quan Môi trường Kinh tế Vĩ mô & Tác động đến Thị trường Chứng khoán Việt Nam")
    
    col_m1, col_m2 = st.columns([1, 1])
    with col_m1:
        st.markdown(f"""
        **Giai đoạn Chu kỳ Kinh tế:** `{macro_analysis.get('cycle_stage', '')}`  
        *Nhận định:* {macro_analysis.get('cycle_desc', '')}
        
        **Định hướng Chính sách Tiền tệ NHNN:** `{macro_analysis.get('monetary_stance', '')}`  
        *Chi tiết:* {macro_analysis.get('monetary_detail', '')}
        
        **Sức hấp dẫn Kênh Đầu tư Cổ phiếu:**  
        `{macro_analysis.get('equity_attractiveness', '')}`  
        *Tỷ trọng khuyến nghị:* **{macro_analysis.get('recommended_equity_weight', '')}**
        """)

        # Bảng chỉ số vĩ mô
        m_df = pd.DataFrame([
            {"Chỉ số": "Tăng trưởng GDP thực tế", "Giá trị": f"{macro_raw.get('gdp_growth_latest_quarter', 7.4):.1f}%", "Mục tiêu / Ý nghĩa": "Mục tiêu cả năm 7.0%"},
            {"Chỉ số": "Lạm phát CPI (YoY)", "Giá trị": f"{macro_raw.get('cpi_yoy', 3.45):.2f}%", "Mục tiêu / Ý nghĩa": "Kiểm soát an toàn dưới 4.0%"},
            {"Chỉ số": "Lãi suất Tái cấp vốn NHNN", "Giá trị": f"{macro_raw.get('refinancing_rate', 4.5):.2f}%", "Mục tiêu / Ý nghĩa": "Mặt bằng thấp lịch sử hỗ trợ vốn"},
            {"Chỉ số": "Tỷ giá USD/VND thị trường", "Giá trị": f"{macro_raw.get('usd_vnd_rate', 25889):,.0f} VND", "Mục tiêu / Ý nghĩa": "Theo sát diễn biến chỉ số DXY"},
            {"Chỉ số": "Lợi suất TPCP 10 năm", "Giá trị": f"{macro_raw.get('gov_bond_10y_yield', 3.2):.2f}%", "Mục tiêu / Ý nghĩa": "Lãi suất phi rủi ro chuẩn (Rf)"},
            {"Chỉ số": "P/E Thị trường VN-Index", "Giá trị": f"{macro_raw.get('vnindex_pe', 14.8):.1f}x", "Mục tiêu / Ý nghĩa": "Lợi suất Earning Yield: 6.76%"},
            {"Chỉ số": "Phần bù rủi ro vốn CP (ERP)", "Giá trị": f"{macro_raw.get('equity_risk_premium', 3.56):.2f}%", "Mục tiêu / Ý nghĩa": "ERP > 3.0% rất hấp dẫn giải ngân"}
        ])
        st.dataframe(m_df, hide_index=True, use_container_width=True)

    with col_m2:
        # Biểu đồ VN-Index
        if not vnindex_df.empty:
            st.markdown(f"**Diễn biến Chỉ số VN-Index (Mốc hiện tại: {macro_raw.get('vnindex_current', 1740):,.1f} điểm)**")
            fig_vn = go.Figure()
            fig_vn.add_trace(go.Scatter(
                x=vnindex_df.index,
                y=vnindex_df["close"],
                mode="lines",
                name="VN-Index",
                line=dict(color="#1A365D", width=2)
            ))
            fig_vn.update_layout(
                height=350,
                margin=dict(l=10, r=10, t=25, b=10),
                template="plotly_white",
                yaxis_title="Điểm số",
                xaxis_title="Thời gian"
            )
            st.plotly_chart(fig_vn, use_container_width=True)

    st.markdown("#### ⚡ Yếu tố Xúc tác & Rủi ro Vĩ mô Cần Theo dõi")
    c_cat, c_risk = st.columns(2)
    with c_cat:
        st.markdown("**Các động lực hỗ trợ thị trường (Catalysts):**")
        for cat in macro_analysis.get("key_catalysts", []):
            st.markdown(f"- ✅ {cat}")
    with c_risk:
        st.markdown("**Các rủi ro vĩ mô cần lưu ý (Macro Risks):**")
        for rk in macro_analysis.get("key_risks", []):
            st.markdown(f"- ⚠️ {rk}")

# ==================== TAB 2: NGÀNH & PEERS ====================
with tab2:
    st.subheader(f"🏭 Phân tích Triển vọng Ngành: {ind_analysis.get('sector_name', '')}")
    
    col_i1, col_i2 = st.columns([1, 1])
    with col_i1:
        st.markdown(f"""
        **Triển vọng Ngành:** `{ind_analysis.get('outlook', '')}`  
        **Giai đoạn Chu kỳ Ngành:** `{ind_analysis.get('cycle_stage', '')}`  
        **Vị thế & Con hào Kinh tế (Moat):** `{ind_analysis.get('competitive_moat', '')}`
        """)
        
        st.markdown("**Động lực tăng trưởng cốt lõi:**")
        for drv in ind_analysis.get("drivers", []):
            st.markdown(f"- 🚀 {drv}")
        
        st.markdown("**Rủi ro ngành trọng yếu:**")
        for rk in ind_analysis.get("risks", []):
            st.markdown(f"- ⚠️ {rk}")

    with col_i2:
        st.markdown("#### 🛡️ Ma trận 5 Áp lực Cạnh tranh (Porter's Five Forces)")
        pf = ind_analysis.get("porter_forces", {})
        for force, desc in pf.items():
            force_vn = {
                "threat_of_entry": "Rào cản gia nhập ngành",
                "supplier_power": "Quyền lực nhà cung cấp",
                "buyer_power": "Quyền lực khách hàng",
                "substitute_threat": "Nguy cơ sản phẩm thay thế",
                "industry_rivalry": "Cạnh tranh nội bộ ngành"
            }.get(force, force)
            st.info(f"**{force_vn}:** {desc}")

    st.markdown("---")
    st.markdown("#### 📊 Bảng So sánh Doanh nghiệp Cùng ngành (Peers Benchmarking)")
    peers = ind_analysis.get("peers", [])
    if peers:
        peers_df = pd.DataFrame(peers)
        peers_df = peers_df.rename(columns={
            "ticker": "Mã CP",
            "name": "Tên Doanh nghiệp",
            "market_cap_bil": "Vốn hóa (Tỷ VNĐ)",
            "pe": "P/E",
            "pb": "P/B",
            "roe": "ROE (%)",
            "rev_growth": "Tăng trưởng DT (%)",
            "market_share": "Thị phần",
            "position": "Vị thế ngành"
        })
        st.dataframe(peers_df, hide_index=True, use_container_width=True)

# ==================== TAB 3: KỸ THUẬT & BCTC ====================
with tab3:
    st.subheader(f"📈 Phân tích Kỹ thuật & Báo cáo Tài chính: {selected_ticker}")
    
    # 1. Biểu đồ nến kỹ thuật tương tác
    if not price_df.empty:
        fig_price = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.75, 0.25])
        
        # Đường nến / giá
        fig_price.add_trace(go.Candlestick(
            x=price_df.index,
            open=price_df["open"],
            high=price_df["high"],
            low=price_df["low"],
            close=price_df["close"],
            name="OHLC",
            increasing_line_color="#2E7D32",
            decreasing_line_color="#C53030"
        ), row=1, col=1)

        # Thêm MA20, MA50
        df_p = price_df.copy()
        df_p["sma20"] = df_p["close"].rolling(20).mean()
        df_p["sma50"] = df_p["close"].rolling(50).mean()
        fig_price.add_trace(go.Scatter(x=df_p.index, y=df_p["sma20"], name="SMA 20", line=dict(color="#DD6B20", width=1.5)), row=1, col=1)
        fig_price.add_trace(go.Scatter(x=df_p.index, y=df_p["sma50"], name="SMA 50", line=dict(color="#319795", width=1.5)), row=1, col=1)

        # Volume
        colors_vol = ["#2E7D32" if c >= o else "#C53030" for c, o in zip(price_df["close"], price_df["open"])]
        fig_price.add_trace(go.Bar(x=price_df.index, y=price_df["volume"], name="Khối lượng", marker_color=colors_vol, opacity=0.8), row=2, col=1)

        fig_price.update_layout(
            height=450,
            margin=dict(l=10, r=10, t=25, b=10),
            template="plotly_white",
            xaxis_rangeslider_visible=False,
            yaxis_title="Giá (VNĐ)",
            yaxis2_title="Khối lượng"
        )
        st.plotly_chart(fig_price, use_container_width=True)

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("#### 📐 Thống kê Kỹ thuật & Rủi ro")
        tech_metrics_df = pd.DataFrame([
            {"Chỉ báo": "Xu hướng Kỹ thuật Tổng hợp", "Giá trị": str(tech_analysis.get("overall_signal", ""))},
            {"Chỉ báo": "Chỉ báo Động lượng RSI (14)", "Giá trị": f"{tech_analysis.get('rsi', 50):.1f} điểm"},
            {"Chỉ báo": "MACD / Signal Line", "Giá trị": f"{tech_analysis.get('macd', 0):.2f} / {tech_analysis.get('macd_signal', 0):.2f}"},
            {"Chỉ báo": "Đường SMA 20 / SMA 50", "Giá trị": f"{tech_analysis.get('sma20', 0):,.0f} / {tech_analysis.get('sma50', 0):,.0f} đ"},
            {"Chỉ báo": "Khối lượng GD / TB 20 phiên", "Giá trị": f"{tech_analysis.get('vol_surge_ratio', 1.0):.2f}x"},
            {"Chỉ báo": "Độ biến động quy năm (Volatility)", "Giá trị": f"{tech_analysis.get('annualized_volatility_pct', 25):.1f}%"},
            {"Chỉ báo": "Hệ số Beta so với VN-Index", "Giá trị": f"{tech_analysis.get('beta', 1.0):.2f}"},
            {"Chỉ báo": "Chỉ số Sharpe (Rf = 3.2%)", "Giá trị": f"{tech_analysis.get('sharpe_ratio', 0.8):.2f}"},
            {"Chỉ báo": "Mức sụt giảm tối đa (MDD)", "Giá trị": f"{tech_analysis.get('max_drawdown_pct', -15):.1f}%"},
            {"Chỉ báo": "Vùng Hỗ trợ / Kháng cự", "Giá trị": f"{tech_analysis.get('support_levels', [0, 0])[0]:,.0f} / {tech_analysis.get('resistance_levels', [0, 0])[0]:,.0f} đ"}
        ])
        st.dataframe(tech_metrics_df, hide_index=True, use_container_width=True)

    with col_t2:
        st.markdown("#### 🔬 Phân tích DuPont 3 Bước & Chất lượng Dòng tiền")
        st.info(f"**Đánh giá DuPont:** {fund_analysis.get('dupont_assessment', '')}")
        st.success(f"**Chất lượng Dòng tiền:** {fund_analysis.get('cf_quality', '')}")
        st.warning(f"**Cơ cấu Đòn bẩy:** {fund_analysis.get('leverage_status', '')}")

        dupont_df = pd.DataFrame([
            {"Nhân tố DuPont": "1. Biên Lợi nhuận ròng (Net Margin)", "Công thức": "LNST / Doanh thu", "Giá trị": f"{fund_analysis.get('net_margin', 0):.1f}%"},
            {"Nhân tố DuPont": "2. Vòng quay Tài sản (Asset Turnover)", "Công thức": "Doanh thu / Tổng tài sản", "Giá trị": f"{fund_analysis.get('asset_turnover', 0):.2f} vòng"},
            {"Nhân tố DuPont": "3. Đòn bẩy Tài chính (Equity Multiplier)", "Công thức": "Tổng tài sản / Vốn CSH", "Giá trị": f"{fund_analysis.get('equity_multiplier', 0):.2f}x"},
            {"Nhân tố DuPont": "👉 Tỷ suất Sinh lời ROE Tổng hợp", "Công thức": "Margin × Turnover × Leverage", "Giá trị": f"{fund_analysis.get('roe', 0):.1f}%"},
            {"Nhân tố DuPont": "Tỷ lệ Dòng tiền OCF / LNST", "Công thức": "Dòng tiền KD / LNST", "Giá trị": f"{fund_analysis.get('ocf_to_ni_ratio', 1.0):.2f}x (>1.0: Xuất sắc)"}
        ])
        st.dataframe(dupont_df, hide_index=True, use_container_width=True)

    # Bảng số liệu BCTC
    st.markdown("#### 📑 Bảng Số liệu Báo cáo Tài chính Qua các Năm (Đơn vị: Tỷ VNĐ)")
    fin_history = stock_raw.get("financial_history", [])
    if fin_history:
        bctc_df = pd.DataFrame(fin_history)
        bctc_df = bctc_df.rename(columns={
            "year": "Năm",
            "revenue": "Doanh thu",
            "gross_profit": "LN Gộp",
            "ebit": "EBIT",
            "net_income": "LNST Cty Mẹ",
            "total_assets": "Tổng Tài sản",
            "equity": "Vốn CSH",
            "debt": "Tổng Nợ vay",
            "cash": "Tiền mặt",
            "ocf": "Dòng tiền OCF",
            "capex": "CapEx",
            "fcf": "Dòng tiền FCF"
        })
        st.dataframe(bctc_df, hide_index=True, use_container_width=True)

# ==================== TAB 4: ĐỊNH GIÁ & SCORECARD ====================
with tab4:
    st.subheader(f"🎯 Mô hình Định giá Đa phương pháp & Quant Multi-Factor Scorecard: {selected_ticker}")
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.markdown("#### ⚖️ Định giá Cổ phiếu Đa Phương pháp")
        v_table_df = pd.DataFrame([
            {"Phương pháp": "1. Định giá theo P/E Mục tiêu", "Giá trị Hợp lý": f"{val_analysis.get('pe_fair_value', 0):,.0f} đ", "Upside (%)": f"+{val_analysis.get('pe_upside', 0):.1f}%", "Trọng số": f"{val_analysis['method_weights']['pe']:.0%}"},
            {"Phương pháp": "2. Định giá theo P/B Mục tiêu", "Giá trị Hợp lý": f"{val_analysis.get('pb_fair_value', 0):,.0f} đ", "Upside (%)": f"+{val_analysis.get('pb_upside', 0):.1f}%", "Trọng số": f"{val_analysis['method_weights']['pb']:.0%}"},
            {"Phương pháp": "3. Chiết khấu Dòng tiền DCF FCFF", "Giá trị Hợp lý": f"{val_analysis.get('dcf_fair_value', 0):,.0f} đ" if val_analysis['dcf_available'] else "Không áp dụng", "Upside (%)": f"{val_analysis.get('dcf_upside', 0):+.1f}%" if val_analysis['dcf_available'] else "—", "Trọng số": f"{val_analysis['method_weights']['dcf']:.0%}"},
            {"Phương pháp": "⭐ GIÁ MỤC TIÊU TỔNG HỢP (BLENDED)", "Giá trị Hợp lý": f"{target_p:,.0f} đ", "Upside (%)": f"+{up_pct:.1f}%", "Trọng số": "100%"}
        ])
        st.dataframe(v_table_df, hide_index=True, use_container_width=True)

        st.markdown(f"**Giả định Mô hình DCF:** WACC: `{val_analysis.get('wacc', 8.5):.2f}%`  |  Chi phí vốn CP Ke: `{val_analysis.get('cost_of_equity', 11.0):.2f}%`  |  Tăng trưởng vĩnh viễn g: `{val_analysis.get('terminal_growth', 3.5):.2f}%`")
        
        # Dự phóng FCFF
        proj_fcf = val_analysis.get("projected_fcf", [])
        if proj_fcf:
            st.markdown("**Dự phóng Dòng tiền FCFF 5 Năm (Tỷ VNĐ):**")
            p_df = pd.DataFrame(proj_fcf).rename(columns={"year": "Năm", "fcf": "Dòng tiền FCFF", "pv": "Hiện giá PV"})
            st.dataframe(p_df, hide_index=True, use_container_width=True)

    with col_v2:
        st.markdown("#### 🎲 Ma trận 3 Kịch bản Đầu tư (Scenario Matrix)")
        bull = scenario_analysis.get("bull_case", {})
        base = scenario_analysis.get("base_case", {})
        bear = scenario_analysis.get("bear_case", {})
        
        scen_df = pd.DataFrame([
            {"Kịch bản": "🚀 TÍCH CỰC (BULL)", "Xác suất": f"{bull.get('probability', 0.25)*100:.0f}%", "Giá Mục tiêu": f"{bull.get('target_price', 0):,.0f} đ", "Tỷ suất": f"+{bull.get('upside_pct', 0):.1f}%", "Giả định": bull.get("assumptions", "")},
            {"Kịch bản": "⚖️ CƠ SỞ (BASE)", "Xác suất": f"{base.get('probability', 0.55)*100:.0f}%", "Giá Mục tiêu": f"{base.get('target_price', 0):,.0f} đ", "Tỷ suất": f"+{base.get('upside_pct', 0):.1f}%", "Giả định": base.get("assumptions", "")},
            {"Kịch bản": "🛡️ THẬN TRỌNG (BEAR)", "Xác suất": f"{bear.get('probability', 0.20)*100:.0f}%", "Giá Mục tiêu": f"{bear.get('target_price', 0):,.0f} đ", "Tỷ suất": f"{bear.get('downside_pct', 0):.1f}%", "Giả định": bear.get("assumptions", "")}
        ])
        st.dataframe(scen_df, hide_index=True, use_container_width=True)

        st.markdown(f"""
        - **Giá trị Kỳ vọng theo Xác suất:** `{scenario_analysis.get('weighted_target_price', 0):,.0f} VNĐ` (+{scenario_analysis.get('weighted_upside_pct', 0):.1f}%)
        - **Tỷ lệ Lợi nhuận / Rủi ro (Risk-Reward):** `{scenario_analysis.get('risk_reward_ratio', 1.5):.2f}x`
        - **Vùng Mua Khuyến nghị:** `{scenario_analysis.get('recommended_buy_zone', '')}`
        - **Ngưỡng Dừng lỗ Bảo toàn vốn (Stop-loss):** `{scenario_analysis.get('stop_loss_price', 0):,.0f} VNĐ`
        """)

    st.markdown("---")
    st.markdown("#### 🏆 Bảng Điểm Định Lượng Toàn Diện (Quant Multi-Factor Scorecard)")
    col_sc1, col_sc2 = st.columns([1, 1])
    
    with col_sc1:
        # Radar Chart trong Streamlit
        pillars = scorecard_analysis.get("pillars", {})
        categories = [p["label"] for p in pillars.values()]
        values_pct = [(p["score"] / p["max"]) * 100 for p in pillars.values()]
        
        categories.append(categories[0])
        values_pct.append(values_pct[0])

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=values_pct,
            theta=categories,
            fill='toself',
            name='Quant Score',
            line_color='#2B6CB0'
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=False,
            height=350,
            margin=dict(l=30, r=30, t=30, b=30)
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with col_sc2:
        score_breakdown = []
        for k, v in pillars.items():
            score_breakdown.append({
                "Trụ cột Đánh giá": v["label"],
                "Điểm đạt": f"{v['score']:.1f}",
                "Thang điểm tối đa": f"{v['max']:.0f}",
                "Tỷ lệ hoàn thành": f"{(v['score']/v['max'])*100:.1f}%"
            })
        st.dataframe(pd.DataFrame(score_breakdown), hide_index=True, use_container_width=True)
        
        st.markdown(f"**Tổng điểm Multi-Factor:** `{total_score:.1f} / 100`  👉  **Xếp hạng:** `{rating}`")
        st.markdown(f"**Chiến lược hành động:** {scorecard_analysis.get('action_guide', '')}")

    st.markdown("##### 📌 Phân tích Điểm mạnh & Rủi ro Từ Scorecard:")
    c_str, c_rsk = st.columns(2)
    with c_str:
        st.markdown("**Điểm mạnh nổi bật (Strengths):**")
        for s in scorecard_analysis.get("strengths", []):
            st.markdown(f"- 🟢 {s}")
    with c_rsk:
        st.markdown("**Rủi ro cần theo dõi (Weaknesses/Risks):**")
        for r in scorecard_analysis.get("risks", []):
            st.markdown(f"- 🔴 {r}")

# ==================== TAB 5: XUẤT BÁO CÁO PDF ====================
with tab5:
    st.subheader(f"📄 Tự Động Tạo Báo Cáo Đầu Tư PDF Chuyên Nghiệp: {selected_ticker}")
    st.markdown("""
    Hệ thống tự động biên soạn và định dạng báo cáo phân tích theo **chuẩn mực của các công ty chứng khoán hàng đầu** 
    (SSI Research, Vietcap, HSC). Báo cáo bao gồm trang bìa tóm tắt điều hành, biểu đồ kỹ thuật và tài chính sắc nét, 
    bảng số liệu định dạng chuẩn, luận điểm đầu tư và tuyên bố miễn trừ trách nhiệm pháp lý.
    """)

    st.markdown("#### 🔍 Xem trước Cấu hình Báo cáo:")
    sec_preview = []
    if inc_macro: sec_preview.append("Bối cảnh Vĩ mô")
    if inc_industry: sec_preview.append("Phân tích Ngành & Cạnh tranh")
    if inc_technical: sec_preview.append("Phân tích Kỹ thuật")
    if inc_fund: sec_preview.append("BCTC & DuPont")
    if inc_val: sec_preview.append("Định giá & Kịch bản")
    if inc_score: sec_preview.append("Quant Multi-Factor Scorecard")

    st.write(f"- **Mã cổ phiếu:** `{selected_ticker}` ({stock_raw.get('name', '')})")
    st.write(f"- **Khung thời gian:** `{timeframe}` | **Ngày phân tích:** `{analysis_date.strftime('%d/%m/%Y')}`")
    st.write(f"- **Các chuyên mục được tích hợp:** {', '.join(sec_preview)}")
    st.write(f"- **Khuyến nghị & Giá mục tiêu:** `{rating}` | `{target_p:,.0f} VNĐ` (+{up_pct:.1f}%)")

    # Nút bấm tạo PDF
    if st.button("🚀 BẮT ĐẦU TẠO BÁO CÁO ĐẦU TƯ PDF", type="primary", use_container_width=True):
        with st.spinner("Đang kết xuất biểu đồ và biên soạn tài liệu PDF..."):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"BaoCao_DauTu_{selected_ticker}_{timestamp}.pdf"
            
            inc_list = []
            if inc_macro: inc_list.append("macro")
            if inc_industry: inc_list.append("industry")
            if inc_technical: inc_list.append("technical")
            if inc_fund: inc_list.append("fundamental")
            if inc_val: inc_list.append("valuation")
            if inc_val: inc_list.append("scenarios")
            if inc_score: inc_list.append("scorecard")

            generated_pdf_path = create_investment_report_pdf(
                ticker=selected_ticker,
                stock_fundamentals=stock_raw,
                fundamental_analysis=fund_analysis,
                technical_analysis=tech_analysis,
                valuation_analysis=val_analysis,
                scorecard_analysis=scorecard_analysis,
                scenario_analysis=scenario_analysis,
                macro_analysis=macro_analysis,
                industry_analysis=ind_analysis,
                price_df=price_df,
                output_filename=pdf_filename,
                included_sections=inc_list,
                analysis_date=analysis_date.strftime("%d/%m/%Y"),
                custom_notes=custom_analyst_notes
            )
            
            st.success(f"✅ Báo cáo PDF đã được tạo thành công: `{pdf_filename}`!")
            
            # Đọc file để tải về
            with open(generated_pdf_path, "rb") as f:
                pdf_bytes = f.read()
            
            st.download_button(
                label=f"📥 TẢI VỀ BÁO CÁO PDF ({os.path.basename(generated_pdf_path)})",
                data=pdf_bytes,
                file_name=pdf_filename,
                mime="application/pdf",
                use_container_width=True
            )

    st.markdown("---")
    st.markdown("#### 📂 Danh sách Báo cáo PDF Đã Được Tạo:")
    report_files = sorted(list(REPORTS_DIR.glob("*.pdf")), key=os.path.getmtime, reverse=True)
    if report_files:
        for rf in report_files[:5]:
            f_size = os.path.getsize(rf) / 1024
            st.markdown(f"- 📄 **{rf.name}** ({f_size:.1f} KB) - *Tạo lúc: {datetime.fromtimestamp(os.path.getmtime(rf)).strftime('%H:%M:%S %d/%m/%Y')}*")
    else:
        st.info("Chưa có file báo cáo nào được tạo.")

