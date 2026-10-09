# HỆ THỐNG PHÂN TÍCH CƠ HỘI ĐẦU TƯ CỔ PHIẾU VIỆT NAM (VIETNAM STOCK ADVISOR)

## KẾT NỐI DNSE TRÊN WINDOWS (CẬP NHẬT 09/10/2026)

Bạn có thể tải toàn bộ mã nguồn xuống bằng **Code → Download ZIP** trên GitHub, hoặc chạy `git pull origin main` ở máy đã clone repo.

1. Mở Terminal trong thư mục dự án. Cài thư viện: `python -m pip install -r requirements.txt`
2. Copy file `.env.example` thành **`.env`** (cùng cấp với `app.py`). Trên PowerShell: `Copy-Item .env.example .env`
3. Mở `.env` trên máy cá nhân, điền hai dòng `DNSE_API_KEY=...` và `DNSE_API_SECRET=...`. Không gửi hai khóa trong chat, không commit `.env` lên GitHub.
4. Chạy `python -m streamlit run app.py`, truy cập http://localhost:8501.
5. Trong sidebar, khi khóa đã được nạp sẽ hiện **Nguồn giá DNSE: đã cấu hình API**. Nhập mã cổ phiếu; bộ tải giá sẽ thử DNSE trước, sau đó Vietcap/VNDirect/Yahoo khi DNSE không khả dụng. Xem dòng **Nguồn giá** để xác nhận dữ liệu đến từ đâu.
6. Kiểm tra mã cụ thể: `python -m unittest tests.test_dnse_loader -v`.

*DNSE cung cấp nguồn giá OHLCV, không mặc nhiên cung cấp bộ BCTC, vĩ mô hoặc các giả định định giá của hệ thống này. Khi API thất bại, chương trình có thể dùng nguồn khác và phải ghi rõ nguồn. Không tự nhận đã kết nối thành công trước khi kiểm tra máy có khóa hợp lệ và có Internet. Dữ liệu vĩ mô/ngành sẵn có trong code có các giả định chưa kiểm chứng; không dùng đầu ra để ra quyết định đầu tư thực.*

---



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
5. **Mô hình Định giá Đa phương pháp:** P/E mục tiêu, P/B mục tiêu, **DCF xấp xỉ từ OCF−CapEx (hai giai đoạn)** với WACC động, và Giá trị mục tiêu tổng hợp (Blended Fair Value).
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

Luồng cổ phiếu dùng nguồn trực tuyến và cache riêng theo mã, có ghi nguồn và thời điểm dữ liệu. Mã không tồn tại hoặc nguồn lỗi sẽ báo thiếu dữ liệu, không tự tạo chuỗi giá hoặc lấy BCTC HPG thay thế.

| Nhóm dữ liệu | Nguồn / tình trạng | Khi thiếu dữ liệu |
| --- | --- | --- |
| Danh sách mã | Vietcap, danh sách tất cả cổ phiếu theo sàn | Cache danh sách hoặc danh mục gợi ý; vẫn cho nhập mã khác |
| Giá OHLCV | DNSE nếu đã cấu hình → Vietcap → VNDirect → Yahoo Finance | Cache `*_prices_v2.json` cùng mã; không có thì báo lỗi |
| BCTC | Vietcap → Yahoo Finance; đối chiếu công bố doanh nghiệp trước khi sử dụng | Cache `*_financials_v2.json` có nguồn; không trộn bộ số liệu mẫu |
| Phân ngành | Thông tin doanh nghiệp từ nguồn tải về | Ngành chưa có mô hình sẽ không mặc định thành ngành thép |
| So sánh ngành | Benchmark và peers trong `industry_loader.py` là dữ liệu/giả định cố định, chưa cập nhật tự động | Không định giá nếu ngành chưa có benchmark phù hợp |
| Vĩ mô | Các chỉ tiêu GDP/CPI/lãi suất trong `macro_loader.py` còn là giá trị cấu hình; chưa có bộ thu thập GSO/SBV đầy đủ | Cần cập nhật và đối chiếu riêng |

Vietcap là API công khai không chính thức, có thể thay đổi hoặc giới hạn truy cập. Cấu trúc endpoint được đối chiếu với mã nguồn [vnstock VCI](https://github.com/thinh-vu/vnstock/tree/main/vnstock/explorer/vci). Kiểm thử tự động dùng mock và fixture, không chứng minh API trực tuyến đang hoạt động cho mọi mã.

### Khuyến nghị theo từng cổ phiếu

- Chọn mã từ danh sách toàn thị trường khi tải được, hoặc nhập `MBB`, `VNM`, `TCB`, `FPT.VN`.
- Nhận xét nêu giá, MA20/MA50, RSI, MACD, thanh khoản, kỳ BCTC, tăng trưởng và định giá của đúng mã đang xem.
- Điểm cao chưa đủ để mua: cần upside phù hợp, lợi nhuận tăng và xu hướng kỹ thuật; quá mua, xu hướng giảm hoặc giá cũ sẽ hạn chế khuyến nghị.
- Thiếu BCTC, dòng tiền, số cổ phiếu lưu hành hoặc benchmark ngành: vẫn xem kỹ thuật và dữ liệu đã tải, không chấm tổng điểm/đưa báo cáo đầu tư đầy đủ.
- Dữ liệu giống nhau có thể cho cùng xếp hạng. Hệ thống không cố tình đổi kết luận chỉ để mỗi mã trông khác nhau.
- `get_preset_fundamentals()` chỉ phục vụ kiểm thử. Cache cũ `*_fundamentals.json` không được dùng vì có thể chứa dữ liệu dự phòng sai mã.

---

## 🧮 5. CÔNG THỨC VÀ NGUYÊN LÝ TÍNH TOÁN

### 5.1. Mô hình Phân tích DuPont 3 Nhân tố
$$ROE = \text{Net Profit Margin} \times \text{Asset Turnover} \times \text{Financial Leverage}$$
Trong đó:
- $\text{Net Profit Margin} = \frac{\text{Lợi nhuận sau thuế}}{\text{Doanh thu thuần}}$
- $\text{Asset Turnover} = \frac{\text{Doanh thu thuần}}{\text{Tổng tài sản}}$
- $\text{Financial Leverage (Equity Multiplier)} = \frac{\text{Tổng tài sản}}{\text{Vốn chủ sở hữu}}$

### 5.2. DCF xấp xỉ (cần chuẩn hóa FCFF khi mở rộng)
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
$$\text{Giá Mục tiêu} = 55\% \times P_{P/B} + 45\% \times P_{P/E}$$

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
- Kiểm thử hiện tại: xem `TEST_RESULTS.md`; chạy `python -m unittest discover -s tests -v` (offline, dùng fixture rõ ràng).

---

## 📋 7. KỊCH BẢN DEMO HỆ THỐNG

1. **Bước 1:** Khởi chạy `py -m streamlit run app.py`.
2. **Bước 2:** Tại thanh bên trái (Sidebar), chọn mã cổ phiếu `HPG` (hoặc `FPT`, `VCB`), chọn khung thời gian `1 Năm`.
3. **Bước 3:** Tab 1 xem đánh giá Vĩ mô Việt Nam (GDP 7.4%, ERP 3.56%, biểu đồ VN-Index).
4. **Bước 4:** Tab 2 xem Triển vọng Ngành, ma trận Porter và bảng so sánh các đối thủ Peers.
5. **Bước 5:** Tab 3 xem Biểu đồ nến tương tác Plotly, các chỉ báo kỹ thuật, Báo cáo tài chính 4 năm và phân tích DuPont.
6. **Bước 6:** Tab 4 xem Kết quả định giá DCF, Ma trận 3 kịch bản Bull/Base/Bear và Radar Chart Quant Scorecard.
7. **Bước 7:** Tab 5 bấm nút **"🚀 BẮT ĐẦU TẠO BÁO CÁO ĐẦU TƯ PDF"** để kết xuất tài liệu PDF 4 trang sắc nét và bấm nút tải về máy tính.


DCF không được đưa vào giá tổng hợp nếu dòng tiền tự do âm, thiếu dữ liệu hoặc thuộc nhóm ngân hàng/chứng khoán. Không đổi dòng tiền âm thành dương để tạo giá mục tiêu. Xác suất 25/55/20 và biên kịch bản là giả định minh họa, chưa được backtest.

Với ngành chưa có benchmark, có thể bật **Tự nhập giả định P/E, P/B ngành** ở thanh bên. Các giá trị được ghi rõ là giả định người dùng, không được gán cho dữ liệu ngành thực tế.
