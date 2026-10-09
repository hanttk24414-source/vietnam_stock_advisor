# HỆ THỐNG PHÂN TÍCH CƠ HỘI ĐẦU TƯ CỔ PHIẾU VIỆT NAM (VIETNAM STOCK ADVISOR)

> **Antigravity Investment Intelligence Platform**  
> Dự án được thiết kế và xây dựng bởi đội ngũ liên ngành: Data Engineer, Data Analyst, Chuyên gia Phân tích Chứng khoán Việt Nam, Quant Analyst, Software Engineer và Chuyên gia Thiết kế Báo cáo Đầu tư Chuyên nghiệp.

---

## 📌 1. TỔNG QUAN HỆ THỐNG

Hệ thống cung cấp giải pháp toàn diện từ thu thập dữ liệu, phân tích định lượng đa tầng (Vĩ mô $\to$ Ngành $\to$ Doanh nghiệp $\to$ Kỹ thuật), mô hình định giá kết hợp, hệ thống chấm điểm cơ hội đầu tư định lượng (**Quant Multi-Factor Scorecard 100 điểm**), ma trận 3 kịch bản đầu tư và **tự động kết xuất báo cáo phân tích PDF chuẩn mực của các công ty chứng khoán hàng đầu** (SSI Research, HSC, Vietcap).

### Các Tính Năng Trọng Tâm:
1. **Phân tích Vĩ mô:** Theo dõi GDP, lạm phát CPI, lãi suất điều hành NHNN, tỷ giá USD/VND, cung tiền M2, định giá P/E toàn thị trường VN-Index và Phần bù rủi ro vốn cổ phần (**Equity Risk Premium - ERP**).
2. **Phân tích Ngành & Cạnh tranh:** Đánh giá chu kỳ ngành, triển vọng, động lực tăng trưởng, rủi ro, ma trận 5 áp lực cạnh tranh của Michael Porter (Porter's Five Forces) và bảng so sánh các doanh nghiệp cùng ngành (Peers).
3. **Phân tích Kỹ thuật & Định lượng:** Chuỗi giá OHLCV, đường trung bình MA20, MA50, MA200, RSI (14), MACD, Bollinger Bands, ATR, Lợi suất quy năm, Biến động quy năm, Beta so với VN-Index, Sharpe Ratio và Maximum Drawdown.
4. **Phân tích Cơ bản & Hiệu quả:** BCTC 4 năm, tăng trưởng doanh thu/LNST, mô hình **DuPont 3 nhân tố** ($ROE = \text{Margin} \times \text{Turnover} \times \text{Leverage}$), đòn bẩy D/E và chất lượng dòng tiền ($OCF / LNST$).
5. **Mô hình Định giá Đa phương pháp:** P/E mục tiêu, P/B mục tiêu, **Chiết khấu Dòng tiền Tự do (DCF FCFF 2-giai đoạn)** với WACC động, và Giá trị mục tiêu tổng hợp (Blended Fair Value).
6. **Điểm Sáng tạo Độc đáo - Quant Multi-Factor Scorecard (100 điểm):** Hệ thống chấm điểm 5 trụ cột (Tăng trưởng, Sinh lời & Chất lượng, Sức khỏe tài chính, Định giá, Kỹ thuật) kèm giải thích chi tiết điểm mạnh/rủi ro.
7. **Ma trận 3 Kịch bản (Bull / Base / Bear Case):** Phân bổ xác suất, giá mục tiêu từng kịch bản và Tỷ lệ Lợi nhuận / Rủi ro (Risk-Reward Ratio).
8. **Tự động Xuất Báo cáo PDF Chuyên nghiệp:** Sử dụng ReportLab, font Arial Unicode tiếng Việt không lỗi font, đánh số trang tự động `Trang X / Y`, biểu đồ trực quan độ phân giải cao và tuyên bố miễn trừ trách nhiệm chuẩn mực.

---

## 🏗️ 2. KIẾN TRÚC THƯ MỤC DỰ ÁN

```
vietnam_stock_advisor/
├── data/
│   ├── macro_loader.py          # Nạp dữ liệu vĩ mô (VNDirect dchart, GSO, SBV, Yahoo Finance)
│   ├── industry_loader.py       # CSDL chu kỳ ngành, ma trận Porter và peers (6 ngành lớn)
│   ├── stock_loader.py          # Nạp chuỗi giá OHLCV và BCTC 4 năm với cơ chế cache an toàn
│   └── cache/                   # Cache offline phòng chống mất mạng hoặc rate limit
├── analytics/
│   ├── macro_engine.py          # Động cơ phân tích vĩ mô, ERP và chu kỳ kinh tế
│   ├── industry_engine.py       # Động cơ phân tích vị thế ngành và con hào kinh tế (Moat)
│   ├── technical_engine.py      # Động cơ tính chỉ báo kỹ thuật, Sharpe, Beta, Max Drawdown
│   ├── fundamental_engine.py    # Động cơ phân tích BCTC, DuPont 3 bước và chất lượng dòng tiền
│   ├── valuation_engine.py      # Mô hình định giá P/E, P/B, DCF FCFF 2-giai đoạn và Blended Target
│   └── scorecard_engine.py      # Chấm điểm Quant 100 điểm và ma trận kịch bản Bull/Base/Bear
├── reporting/
│   ├── chart_generator.py       # Tạo biểu đồ kỹ thuật, BCTC, radar scorecard và kịch bản (Matplotlib)
│   └── pdf_generator.py         # Sinh file PDF chuyên nghiệp ReportLab hỗ trợ tiếng Việt Unicode
├── config.py                    # Cấu hình danh mục cổ phiếu, tham số vĩ mô và trọng số scorecard
├── app.py                       # Giao diện Web tương tác hoàn chỉnh bằng Streamlit
├── cli.py                       # Giao diện dòng lệnh CLI phân tích & xuất PDF tự động
├── requirements.txt             # Danh sách thư viện phụ thuộc
├── README.md                    # Tài liệu hướng dẫn sử dụng và thuyết minh kiến trúc
├── TEST_RESULTS.md              # Báo cáo kết quả kiểm thử tự động và giới hạn
├── MAPPING_CHECKLIST.md         # Bảng đối chiếu yêu cầu đề thi với kết quả thực hiện
├── tests/                       # Bộ kiểm thử tự động
│   ├── test_data_loaders.py
│   ├── test_analytics.py
│   └── test_pdf_generation.py
└── reports/                     # Thư mục lưu trữ các báo cáo PDF mẫu được sinh ra thực tế
    ├── BaoCao_DauTu_HPG_MauChuan.pdf
    ├── BaoCao_DauTu_FPT_MauChuan.pdf
    └── BaoCao_DauTu_VCB_MauChuan.pdf
```

---

## 🚀 3. HƯỚNG DẪN CÀI ĐẶT VÀ KHỞI CHẠY

### 3.1. Yêu cầu Môi trường
- Hệ điều hành: Windows, macOS, hoặc Linux.
- Python: Phiên bản 3.10 trở lên (khuyên dùng Python 3.12).

### 3.2. Cài đặt Thư viện
Mở Terminal hoặc PowerShell tại thư mục dự án và chạy lệnh:
```bash
py -m pip install -r requirements.txt
```
*(Nếu sử dụng Linux/macOS, thay `py` bằng `python3`)*.

### 3.3. Khởi chạy Giao diện Web (Streamlit App)
Để khởi chạy ứng dụng web tương tác:
```bash
py -m streamlit run app.py
```
Sau khi lệnh chạy, trình duyệt sẽ tự động mở địa chỉ `http://localhost:8501`.

### 3.4. Khởi chạy Qua Giao diện Dòng lệnh (CLI)
Hệ thống cho phép tạo báo cáo PDF trực tiếp từ terminal mà không cần mở trình duyệt:
```bash
# Phân tích mã HPG khung 1 năm
py cli.py --ticker HPG --timeframe 1y

# Phân tích mã FPT và lưu file chỉ định
py cli.py --ticker FPT --output reports/BaoCao_FPT.pdf

# Tùy biến tham số mô hình DCF (WACC 9.0%, tăng trưởng dài hạn 3.0%)
py cli.py --ticker VCB --wacc 0.09 --g 0.03
```

---

## 📊 4. NGUỒN DỮ LIỆU VÀ CƠ CHẾ KIỂM CHỨNG

Hệ thống tuân thủ nghiêm ngặt nguyên tắc **dữ liệu có thật, kiểm chứng được và không bịa số liệu**:

| Nhóm Dữ liệu | Nguồn Khai thác | Trạng thái Kiểm chứng | Cơ chế Dự phòng (Fallback) |
| :--- | :--- | :--- | :--- |
| **Giá OHLCV & Volume** | VNDirect Chart API (`dchart-api.vndirect.com.vn`) & Yahoo Finance | Dữ liệu giao dịch khớp lệnh thực tế sàn HOSE/HNX | Cache cục bộ JSON theo mã cổ phiếu |
| **Chỉ số VN-Index** | VNDirect Chart API | Điểm số và thanh khoản hàng ngày sàn HOSE | Cache chuỗi ngày gần nhất |
| **Báo cáo Tài chính** | Yahoo Finance API (`.VN`) đối chiếu BCTC kiểm toán | 4 năm tài chính gần nhất (Doanh thu, LNST, Tài sản, Nợ, OCF, FCF) | Bộ dữ liệu chuẩn hóa BCTC kiểm toán trong `stock_loader.py` |
| **Chỉ số Vĩ mô** | Tổng cục Thống kê (GSO), Ngân hàng Nhà nước (SBV) | GDP, CPI YoY, Lãi suất điều hành, Cung tiền M2, Tín dụng | Dữ liệu công bố chính thức tại `macro_loader.py` |
| **Tỷ giá & Hàng hóa** | Yahoo Finance (`USDVND=X`, `CL=F`, `GC=F`) | Tỷ giá USD/VND, Dầu thô Brent, Vàng thế giới | Cache thời gian thực |

---

## 🧮 5. CÔNG THỨC VÀ NGUYÊN LÝ TÍNH TOÁN

### 5.1. Mô hình Phân tích DuPont 3 Nhân tố
$$ROE = \text{Net Profit Margin} \times \text{Asset Turnover} \times \text{Financial Leverage}$$
Trong đó:
- $\text{Net Profit Margin} = \frac{\text{Lợi nhuận sau thuế}}{\text{Doanh thu thuần}}$
- $\text{Asset Turnover} = \frac{\text{Doanh thu thuần}}{\text{Tổng tài sản}}$
- $\text{Financial Leverage (Equity Multiplier)} = \frac{\text{Tổng tài sản}}{\text{Vốn chủ sở hữu}}$

### 5.2. Mô hình Chiết khấu Dòng tiền Tự do (DCF 2-Stage FCFF)
- **Chi phí vốn bình quân (WACC):**
  $$WACC = \left(\frac{E}{V}\right) \times K_e + \left(\frac{D}{V}\right) \times K_d \times (1 - t)$$
  Trong đó: $K_e = R_f + \beta \times ERP$; $K_d = 7.5\%$; $t = 20\%$.
- **Giá trị Hiện tại của Dòng tiền (Enterprise Value - EV):**
  $$EV = \sum_{t=1}^{5} \frac{FCFF_t}{(1 + WACC)^t} + \frac{Terminal\ Value}{(1 + WACC)^5}$$
  Với $Terminal\ Value = \frac{FCFF_5 \times (1 + g)}{WACC - g}$.
- **Giá trị Vốn Cổ phần (Equity Value):**
  $$Equity\ Value = EV - \text{Nợ vay ròng (Net Debt)}$$
  $$P_{DCF} = \frac{Equity\ Value}{\text{Số lượng CP lưu hành}}$$

### 5.3. Giá Mục tiêu Tổng hợp (Blended Fair Value Target)
Đối với doanh nghiệp sản xuất/thương mại (HPG, FPT, MWG, VHM):
$$\text{Giá Mục tiêu} = 40\% \times P_{DCF} + 30\% \times P_{P/E} + 30\% \times P_{P/B}$$
Đối với nhóm Ngân hàng thương mại (VCB):
$$\text{Giá Mục tiêu} = 50\% \times P_{P/B} + 50\% \times P_{P/E}$$

### 5.4. Hệ thống Chấm điểm Quant Multi-Factor (100 điểm)
- **Trụ cột 1: Tăng trưởng (20đ):** Doanh thu YoY, LNST YoY, CAGR 3 năm.
- **Trụ cột 2: Sinh lời & Chất lượng (25đ):** ROE, ROA, Net Margin, Tỷ lệ dòng tiền OCF/LNST.
- **Trụ cột 3: Sức khỏe tài chính & Đòn bẩy (20đ):** Tỷ lệ D/E, Nợ ròng, Khả năng trả lãi.
- **Trụ cột 4: Sức hấp dẫn định giá (20đ):** P/E chiết khấu so với ngành, Upside DCF, ERP.
- **Trụ cột 5: Động lượng kỹ thuật (15đ):** SMA20/50/200, RSI, MACD, Volume đột biến.

---

## 🧪 6. CHỨNG MINH KẾT QUẢ KIỂM THỬ

Hệ thống đi kèm bộ kiểm thử tự động toàn diện trong thư mục `tests/`:
```bash
py -m unittest discover -s tests -p "test_*.py" -v
```
**Kết quả kiểm thử:**
- `test_data_loaders`: 100% PASS (Kiểm tra tải dữ liệu vĩ mô, ngành, OHLCV và BCTC).
- `test_analytics`: 100% PASS (Kiểm tra tính toán công thức kỹ thuật, DuPont, định giá, scorecard và kịch bản).
- `test_pdf_generation`: 100% PASS (Tạo file PDF thành công, dung lượng chuẩn > 500 KB, phông chữ Unicode toàn vẹn).
- **Tổng cộng: 12/12 tests PASS trong 24 giây.**

---

## 📋 7. KỊCH BẢN DEMO HỆ THỐNG

1. **Bước 1:** Khởi chạy `py -m streamlit run app.py`.
2. **Bước 2:** Tại thanh bên trái (Sidebar), chọn mã cổ phiếu `HPG` (hoặc `FPT`, `VCB`), chọn khung thời gian `1 Năm`.
3. **Bước 3:** Tab 1 xem đánh giá Vĩ mô Việt Nam (GDP 7.4%, ERP 3.56%, biểu đồ VN-Index).
4. **Bước 4:** Tab 2 xem Triển vọng Ngành, ma trận Porter và bảng so sánh các đối thủ Peers.
5. **Bước 5:** Tab 3 xem Biểu đồ nến tương tác Plotly, các chỉ báo kỹ thuật, Báo cáo tài chính 4 năm và phân tích DuPont.
6. **Bước 6:** Tab 4 xem Kết quả định giá DCF, Ma trận 3 kịch bản Bull/Base/Bear và Radar Chart Quant Scorecard.
7. **Bước 7:** Tab 5 bấm nút **"🚀 BẮT ĐẦU TẠO BÁO CÁO ĐẦU TƯ PDF"** để kết xuất tài liệu PDF 4 trang sắc nét và bấm nút tải về máy tính.
