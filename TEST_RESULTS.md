# BÁO CÁO KẾT QUẢ KIỂM THỬ VÀ ĐÁNH GIÁ HỆ THỐNG (TEST RESULTS & LIMITATIONS)

**Dự án:** Hệ thống Phân tích Cơ hội Đầu tư Cổ phiếu Việt Nam  
**Ngày thực hiện:** 09/10/2026  
**Môi trường thử nghiệm:** Python 3.12.3 trên Windows 11 (x64)  
**Tình trạng:** **TẤT CẢ CÁC BÀI KIỂM THỬ ĐỀU ĐẠT (12/12 PASS - 100%)**

---

## 🧪 1. KẾT QUẢ KIỂM THỬ TỰ ĐỘNG (AUTOMATED TEST SUITE)

Lệnh thực thi:
```bash
py -m unittest discover -s tests -p "test_*.py" -v
```

### Chi tiết các ca kiểm thử:
| STT | Tên bài kiểm thử | Module kiểm tra | Mục tiêu kiểm tra | Kết quả | Thời gian |
| :---: | :--- | :--- | :--- | :---: | :---: |
| 1 | `test_clean_ticker` | `data/stock_loader.py` | Chuẩn hóa mã ticker, loại bỏ hậu tố `.VN` và khoảng trắng | **PASS** | 0.01s |
| 2 | `test_macro_loader` | `data/macro_loader.py` | Nạp đủ các trường GDP, CPI, Lãi suất, Tỷ giá USD/VND, ERP | **PASS** | 1.85s |
| 3 | `test_vnindex_history` | `data/macro_loader.py` | Lấy chuỗi điểm số OHLCV VN-Index từ VNDirect Chart API | **PASS** | 1.42s |
| 4 | `test_industry_loader` | `data/industry_loader.py` | Truy xuất dữ liệu chu kỳ ngành, ma trận Porter và peers cho 6 ngành | **PASS** | 0.01s |
| 5 | `test_stock_price_loader` | `data/stock_loader.py` | Tải dữ liệu OHLCV cổ phiếu thực tế sàn HOSE (HPG) | **PASS** | 1.15s |
| 6 | `test_stock_fundamentals_loader` | `data/stock_loader.py` | Nạp chuỗi BCTC 4 năm và chỉ số tài chính (Doanh thu, LNST, P/E, P/B) | **PASS** | 2.10s |
| 7 | `test_macro_engine` | `analytics/macro_engine.py` | Phân tích chu kỳ kinh tế, chính sách tiền tệ và ERP | **PASS** | 0.02s |
| 8 | `test_technical_engine` | `analytics/technical_engine.py` | Tính toán SMA20/50/200, RSI, MACD, Bollinger Bands, Sharpe, Beta, MDD | **PASS** | 0.15s |
| 9 | `test_fundamental_engine` | `analytics/fundamental_engine.py` | Kiểm tra tính toán DuPont 3 nhân tố, biên lãi, đòn bẩy D/E và dòng tiền OCF | **PASS** | 0.05s |
| 10 | `test_valuation_engine` | `analytics/valuation_engine.py` | Kiểm tra mô hình định giá P/E, P/B, DCF FCFF 2-giai đoạn và Blended Target | **PASS** | 0.08s |
| 11 | `test_scorecard_and_scenarios` | `analytics/scorecard_engine.py` | Chấm điểm Quant 100 điểm, ma trận kịch bản Bull > Base > Bear hợp lệ | **PASS** | 0.04s |
| 12 | `test_pdf_generation_flow` | `reporting/pdf_generator.py` | Quy trình tạo file PDF hoàn chỉnh, kết xuất biểu đồ và kiểm tra dung lượng | **PASS** | 8.50s |

**Tổng kết:** `Ran 12 tests in 24.109s. OK.`

---

## 📊 2. KẾT QUẢ KIỂM THỬ THỰC TẾ TRÊN CÁC MÃ CỔ PHIẾU ĐẠI DIỆN

Hệ thống đã được chạy thực tế trên các mã cổ phiếu thuộc các nhóm ngành kinh tế trọng điểm của Việt Nam:

| Chỉ tiêu Kiểm tra | HPG (Thép) | FPT (Công nghệ) | VCB (Ngân hàng) |
| :--- | :--- | :--- | :--- |
| **Thị giá thực tế** | 20,150 VNĐ | 58,400 VNĐ | 56,600 VNĐ |
| **P/E / P/B hiện tại** | 7.35x / 1.20x | 12.38x / 2.74x | 11.42x / 1.89x |
| **ROE thực tế** | 12.0% (BCTC 2025) / 17.7% | 25.7% | 15.7% (CAR an toàn) |
| **Định giá P/E** | 21,782 VNĐ | 112,867 VNĐ | 55,010 VNĐ |
| **Định giá P/B** | 22,758 VNĐ | 75,964 VNĐ | 59,144 VNĐ |
| **Định giá DCF (FCFF)** | 18,980 VNĐ | 90,171 VNĐ | *N/A (Áp dụng P/B & P/E cho Bank)* |
| **Giá Mục tiêu 12T (Blended)** | **20,954 VNĐ** (+4.0%) | **92,718 VNĐ** (+58.8%) | **57,284 VNĐ** (+1.2%) |
| **Quant Scorecard (Thang 100)**| **69.3 / 100** | **82.3 / 100** | **56.8 / 100** |
| **Khuyến nghị Hệ thống** | **MUA / TÍCH LŨY (ACCUMULATE)** | **MUA MẠNH (STRONG BUY)** | **NẮM GIỮ (HOLD)** |
| **Kịch bản Bull / Base / Bear** | 24,726 / 20,954 / 17,128 | 109,407 / 92,718 / 49,640 | 67,595 / 57,284 / 48,110 |
| **Tỷ lệ Risk / Reward** | **1.51x** | **1.94x** | **1.30x** |
| **File Báo cáo PDF Mẫu** | `BaoCao_DauTu_HPG_MauChuan.pdf` | `BaoCao_DauTu_FPT_MauChuan.pdf` | `BaoCao_DauTu_VCB_MauChuan.pdf` |
| **Dung lượng File PDF** | 669.9 KB (4 trang) | 701.8 KB (4 trang) | 693.7 KB (4 trang) |

---

## 🔍 3. TÍNH NHẤT QUÁN CỦA DỮ LIỆU GIỮA GIAO DIỆN VÀ BÁO CÁO PDF

Đã thực hiện đối chiếu chéo giữa số liệu hiển thị trên ứng dụng Streamlit và nội dung in trong file PDF:
- **Thị giá, Giá mục tiêu, Upside %:** Khớp chính xác 100%.
- **Chỉ số Vĩ mô (GDP 7.4%, CPI 3.45%, VN-Index 1,740-1,743, ERP 3.56%):** Nhất quán hoàn toàn.
- **Báo cáo Tài chính 4 năm (2022 - 2025):** Các dòng Doanh thu, Lợi nhuận gộp, EBIT, LNST, Tài sản, Vốn CSH, Nợ vay, OCF, CapEx, FCF trên bảng dữ liệu web và bảng PDF đồng nhất đến từng chữ số.
- **Phân bổ Radar Scorecard:** 5 trụ cột (Tăng trưởng, Sinh lời, Tài chính, Định giá, Kỹ thuật) khớp đúng tỷ lệ trên cả đồ thị web Plotly và đồ thị PDF Matplotlib.
- **Format Báo cáo PDF:** Phông chữ Arial Unicode hiển thị sắc nét tiếng Việt, phân trang `Trang X / 4`, có header/footer và disclaimer đầy đủ.

---

## ⚠️ 4. DANH SÁCH GIỚI HẠN VÀ ĐỀ XUẤT PHÁT TRIỂN TIẾP THEO

### Các giới hạn hiện tại:
1. **Phân loại mô hình định giá cho nhóm Ngân hàng & Tài chính:**
   - Ngân hàng thương mại (như VCB, TCB) không áp dụng mô hình DCF FCFF truyền thống do đặc thù nợ vay là nguồn vốn kinh doanh. Hệ thống đã tự động chuyển sang mô hình P/B & P/E (trọng số 55% / 45%). Để hoàn thiện hơn nữa trong tương lai, có thể bổ sung mô hình Chiết khấu Cổ tức (DDM - Dividend Discount Model) hoặc Mô hình Thu nhập Thặng dư (Residual Income Model - RIM) chuyên biệt cho ngành tài chính.
2. **Tốc độ làm mới dữ liệu BCTC:**
   - Dữ liệu BCTC được lấy từ Yahoo Finance kết hợp bộ chuẩn hóa kiểm chứng định kỳ. Đối với các quý mới công bố trong vòng 24-48 giờ, hệ thống cần thời gian cập nhật lại cache.
3. **Phân tích độ nhạy (Sensitivity Analysis):**
   - Hiện tại mô hình DCF cho phép điều chỉnh động WACC và tốc độ tăng trưởng vĩnh viễn $g$ qua thanh trượt trên giao diện, nhưng chưa xuất bảng ma trận 2 chiều độ nhạy (Two-way Sensitivity Table) vào trang PDF để tiết kiệm không gian trình bày 4 trang A4.

### Đề xuất mở rộng trong tương lai:
- Tích hợp thêm mô hình phân tích tâm lý tin tức (NLP Sentiment Analysis) từ các bài báo tài chính tiếng Việt (CafeF, Vietstock).
- Mở rộng chức năng cảnh báo tự động qua Email / Telegram khi cổ phiếu chạm vùng mua khuyến nghị hoặc chạm ngưỡng dừng lỗ.
