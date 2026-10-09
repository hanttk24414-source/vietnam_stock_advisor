"""
Module phân tích và chuẩn hóa dữ liệu ngành tại thị trường chứng khoán Việt Nam.
Cung cấp bức tranh toàn cảnh về chu kỳ ngành, động lực tăng trưởng, rủi ro,
ma trận 5 áp lực cạnh tranh (Porter's Five Forces) và bảng so sánh các cổ phiếu cùng ngành (Peers).
"""

from typing import Dict, Any, List

INDUSTRY_DATABASE: Dict[str, Dict[str, Any]] = {
    "STEEL": {
        "name": "Thép & Vật liệu xây dựng",
        "cycle_stage": "Giai đoạn Phục hồi & Tăng tốc Chu kỳ Mới",
        "outlook": "Khả quan - Đón đầu chu kỳ đầu tư công & Bất động sản phục hồi",
        "benchmark_pe": 10.8,
        "benchmark_pb": 1.35,
        "benchmark_roe": 15.2,
        "drivers": [
            "Đẩy mạnh giải ngân vốn đầu tư công hạ tầng (Cao tốc Bắc - Nam, Sân bay Long Thành, Vành đai 3 & 4).",
            "Luật Đất đai 2024 có hiệu lực kích hoạt hàng loạt dự án bất động sản dân dụng khởi công trở lại.",
            "Dự án Khu liên hợp gang thép Dung Quất 2 đi vào vận hành giúp nâng công suất HRC thêm 5.6 triệu tấn/năm, gia tăng biên lợi nhuận và thị phần.",
            "Xuất khẩu thép chất lượng cao sang các thị trường lớn như EU, Hoa Kỳ và Đông Nam Á duy trì tăng trưởng tích cực."
        ],
        "risks": [
            "Áp lực cạnh tranh từ thép cuộn cán nóng (HRC) giá rẻ nhập khẩu từ Trung Quốc.",
            "Biến động giá nguyên liệu đầu vào toàn cầu (quặng sắt 62% Fe, than mỡ luyện cốc coke).",
            "Các cuộc điều tra phòng vệ thương mại, chống bán phá giá tại thị trường xuất khẩu."
        ],
        "porter_forces": {
            "threat_of_entry": "Thấp (Rào cản vốn khổng lồ hàng tỷ USD, yêu cầu công nghệ luyện thép lò cao BOF khép kín)",
            "supplier_power": "Trung bình (Phụ thuộc nhập khẩu quặng sắt và than cốc, nhưng các tập đoàn lớn có năng lực đàm phán cao)",
            "buyer_power": "Trung bình (Khách hàng phân tán gồm các nhà thầu xây dựng, đại lý phân phối cấp 1 và nhà máy tôn mạ)",
            "substitute_threat": "Rất thấp (Vật liệu kim loại kết cấu chịu lực trong xây dựng và chế tạo máy chưa có sản phẩm thay thế tương đương)",
            "industry_rivalry": "Trung bình - Thấp đối với nhóm dẫn đầu (Thị phần tập trung vào số ít doanh nghiệp top đầu có lợi thế quy mô)"
        },
        "peers": [
            {"ticker": "HPG", "name": "Hòa Phát", "market_cap_bil": 146000, "pe": 7.35, "pb": 1.20, "roe": 17.7, "rev_growth": 53.6, "market_share": "38.5% thép xây dựng, 35% HRC", "position": "Thống lĩnh thị trường"},
            {"ticker": "HSG", "name": "Hoa Sen", "market_cap_bil": 13200, "pe": 14.2, "pb": 1.25, "roe": 9.1, "rev_growth": 14.5, "market_share": "28.0% tôn mạ", "position": "Số 1 mảng Tôn mạ"},
            {"ticker": "NKG", "name": "Nam Kim", "market_cap_bil": 5800, "pe": 12.8, "pb": 1.05, "roe": 8.4, "rev_growth": 11.2, "market_share": "16.5% tôn mạ", "position": "Mạnh về xuất khẩu"}
        ]
    },
    "TECH": {
        "name": "Công nghệ thông tin & Viễn thông",
        "cycle_stage": "Giai đoạn Tăng trưởng Bền vững (Secular Growth)",
        "outlook": "Rất khả quan - Làn sóng Chuyển đổi số toàn cầu & AI/Bán dẫn",
        "benchmark_pe": 18.5,
        "benchmark_pb": 3.20,
        "benchmark_roe": 25.5,
        "drivers": [
            "Chi tiêu CNTT toàn cầu tiếp tục tăng mạnh vào các lĩnh vực Điện toán đám mây (Cloud), AI và An toàn thông tin.",
            "Mở rộng hợp tác chiến lược với NVIDIA xây dựng AI Factory, đào tạo nhân lực bán dẫn và thiết kế vi mạch.",
            "Doanh thu ký mới dịch vụ IT tại thị trường nước ngoài (Mỹ, Nhật Bản, Châu Âu) duy trì đà tăng trưởng 20-25%/năm.",
            "Thế mạnh cạnh tranh vượt trội về nguồn nhân lực trẻ, chi phí tối ưu và chất lượng chuẩn quốc tế."
        ],
        "risks": [
            "Nguy cơ suy thoái kinh tế ở Mỹ và Châu Âu có thể khiến các tập đoàn trì hoãn ngân sách đầu tư công nghệ lớn.",
            "Cạnh tranh gay gắt về nguồn nhân lực công nghệ thông tin và AI chất lượng cao.",
            "Biến động tỷ giá JPY/VND ảnh hưởng đến biên lợi nhuận chuyển đổi từ thị trường Nhật Bản."
        ],
        "porter_forces": {
            "threat_of_entry": "Trung bình - Cao (Đòi hỏi bề dày chứng chỉ quốc tế, quan hệ khách hàng Fortune 500 và quy mô hàng chục nghìn kỹ sư)",
            "supplier_power": "Thấp (Nguồn cung phần cứng và nền tảng đám mây đa dạng)",
            "buyer_power": "Trung bình (Khách hàng doanh nghiệp quốc tế có tiêu chuẩn khắt khe nhưng chi phí chuyển đổi nhà cung cấp cao)",
            "substitute_threat": "Thấp (Chuyển đổi số và AI là xu thế bắt buộc sống còn của doanh nghiệp toàn cầu)",
            "industry_rivalry": "Vừa phải (Các doanh nghiệp Việt Nam chủ yếu cạnh tranh trên thị trường toàn cầu với các công ty Ấn Độ, Đông Âu)"
        },
        "peers": [
            {"ticker": "FPT", "name": "Tập đoàn FPT", "market_cap_bil": 85000, "pe": 12.38, "pb": 2.74, "roe": 27.1, "rev_growth": 19.5, "market_share": "Số 1 xuất khẩu phần mềm", "position": "Tập đoàn công nghệ dẫn đầu"},
            {"ticker": "CMG", "name": "CMC Corp", "market_cap_bil": 7800, "pe": 19.5, "pb": 2.10, "roe": 12.4, "rev_growth": 12.8, "market_share": "Top 2 giải pháp hạ tầng số", "position": "Mạnh về hạ tầng & Cloud"},
            {"ticker": "ELC", "name": "Elcom", "market_cap_bil": 1950, "pe": 11.2, "pb": 1.45, "roe": 14.5, "rev_growth": 22.0, "market_share": "Dẫn đầu giao thông thông minh", "position": "Ngách ITS & Viễn thông"}
        ]
    },
    "BANKING": {
        "name": "Ngân hàng Thương mại",
        "cycle_stage": "Giai đoạn Tăng trưởng Ổn định & Kiểm soát Rủi ro",
        "outlook": "Khả quan - Hưởng lợi từ sự phục hồi của nền kinh tế thực",
        "benchmark_pe": 9.2,
        "benchmark_pb": 1.55,
        "benchmark_roe": 18.8,
        "drivers": [
            "Tín dụng toàn hệ thống tăng trưởng mục tiêu 15%, đáp ứng nhu cầu vốn phục hồi sản xuất và tiêu dùng.",
            "Biên lãi thuần (NIM) duy trì ổn định nhờ chi phí vốn huy động được kiểm soát tốt và tỷ lệ tiền gửi không kỳ hạn (CASA) cao.",
            "Tăng trưởng doanh thu từ phí dịch vụ ngân hàng số, bảo hiểm (bancassurance) và tài trợ thương mại.",
            "Tỷ lệ an toàn vốn (CAR) theo chuẩn mực Basel II/III duy trì ở mức cao vững chắc."
        ],
        "risks": [
            "Áp lực nợ xấu (NPL) tiềm ẩn sau khi Thông tư 02 hết hiệu lực, đòi hỏi gia tăng trích lập dự phòng.",
            "Thị trường bất động sản hồi phục chưa đồng đều có thể ảnh hưởng đến khả năng thanh toán của một số chủ đầu tư.",
            "Cạnh tranh lãi suất cho vay làm co hẹp biên lãi ròng ở nhóm khách hàng chất lượng cao."
        ],
        "porter_forces": {
            "threat_of_entry": "Rất thấp (Ngân hàng Nhà nước kiểm soát nghiêm ngặt việc cấp phép thành lập mới; yêu cầu vốn pháp định cao)",
            "supplier_power": "Trung bình (Người gửi tiền có nhiều lựa chọn, nhưng ngân hàng uy tín giữ chân được tệp khách hàng trung thành)",
            "buyer_power": "Trung bình (Người đi vay tìm kiếm lãi suất ưu đãi, song thủ tục thẩm định và giải ngân quyết định sự gắn kết)",
            "substitute_threat": "Thấp (Các kênh Fintech và ví điện tử chủ yếu đóng vai trò trung gian thanh toán, chưa thể thay thế dịch vụ tín dụng)",
            "industry_rivalry": "Cao (Cạnh tranh gay gắt về lãi suất cho vay, chuyển đổi số và phát triển dịch vụ ngân hàng bán lẻ)"
        },
        "peers": [
            {"ticker": "VCB", "name": "Vietcombank", "market_cap_bil": 314000, "pe": 11.42, "pb": 1.89, "roe": 18.0, "rev_growth": 51.6, "market_share": "Chất lượng tài sản số 1, CASA > 34%", "position": "Anh cả ngành ngân hàng"},
            {"ticker": "TCB", "name": "Techcombank", "market_cap_bil": 88000, "pe": 7.8, "pb": 1.15, "roe": 16.5, "rev_growth": 18.2, "market_share": "CASA top 1 ~ 40%, mạnh mảng BĐS", "position": "Ngân hàng tư nhân hàng đầu"},
            {"ticker": "MBB", "name": "MBBank", "market_cap_bil": 115000, "pe": 6.9, "pb": 1.25, "roe": 22.1, "rev_growth": 21.0, "market_share": "Khách hàng số dẫn đầu, CASA cao", "position": "Hiệu quả sinh lời vượt trội"}
        ]
    },
    "RETAIL": {
        "name": "Bán lẻ & Tiêu dùng",
        "cycle_stage": "Giai đoạn Tăng tốc Hồi phục Tiêu dùng Nội địa",
        "outlook": "Tích cực - Sức mua hồi phục & Tái cấu trúc chuỗi tối ưu biên lợi nhuận",
        "benchmark_pe": 15.0,
        "benchmark_pb": 2.80,
        "benchmark_roe": 24.0,
        "drivers": [
            "Chính sách giảm thuế VAT 2% và cải cách tiền lương thúc đẩy tổng mức bán lẻ hàng hóa và doanh thu dịch vụ tiêu dùng.",
            "Chuỗi bán lẻ bách hóa (Bách Hóa Xanh, WinCommerce) đạt điểm hòa vốn và bắt đầu đóng góp lợi nhuận dương đáng kể.",
            "Tái cấu trúc tinh gọn mạng lưới cửa hàng, đóng các điểm bán kém hiệu quả giúp tối ưu hóa chi phí SG&A.",
            "Tiếp tục mở rộng mạng lưới bán lẻ dược phẩm hiện đại (Long Châu, An Khang)."
        ],
        "risks": [
            "Sức mua phân khúc hàng hóa điện máy công nghệ cao (ICT/CE) phục hồi chậm hơn kỳ vọng.",
            "Áp lực cạnh tranh khốc liệt từ sàn thương mại điện tử (Shopee, Lazada, TikTok Shop).",
            "Biến động chi phí logistics và mặt bằng bán lẻ tại các đô thị lớn."
        ],
        "porter_forces": {
            "threat_of_entry": "Trung bình (Rào cản gia nhập ở mảng chuỗi bán lẻ hiện đại là năng lực chuỗi cung ứng và hệ thống logistics)",
            "supplier_power": "Thấp (Các nhà bán lẻ đầu ngành có ưu thế vượt trội khi đàm phán chiết khấu thương mại và công nợ với nhà cung cấp)",
            "buyer_power": "Cao (Người tiêu dùng có độ nhạy cảm cao về giá cả và khuyến mãi)",
            "substitute_threat": "Trung bình - Cao (Chợ truyền thống và các nền tảng thương mại điện tử là kênh cạnh tranh trực tiếp)",
            "industry_rivalry": "Cao (Cạnh tranh gay gắt về giá bán, chất lượng dịch vụ khách hàng và chính sách hậu mãi)"
        },
        "peers": [
            {"ticker": "MWG", "name": "Thế Giới Di Động", "market_cap_bil": 110000, "pe": 11.14, "pb": 3.11, "roe": 30.1, "rev_growth": 29.6, "market_share": "50% ICT/CE, top 1 chuỗi Bách Hóa", "position": "Thống lĩnh bán lẻ đa chuỗi"},
            {"ticker": "FRT", "name": "FPT Retail", "market_cap_bil": 22000, "pe": 28.5, "pb": 6.80, "roe": 19.5, "rev_growth": 26.0, "market_share": "Dẫn đầu bán lẻ dược phẩm Long Châu", "position": "Ngôi sao tăng trưởng dược phẩm"},
            {"ticker": "PNJ", "name": "Vàng bạc Đá quý Phú Nhuận", "market_cap_bil": 31000, "pe": 14.5, "pb": 2.90, "roe": 22.0, "rev_growth": 14.2, "market_share": ">55% thị trường trang sức có thương hiệu", "position": "Thống lĩnh thị trường trang sức"}
        ]
    },
    "BROKERAGE": {
        "name": "Dịch vụ Tài chính & Chứng khoán",
        "cycle_stage": "Giai đoạn Hưởng lợi Trực tiếp từ Chu kỳ Nâng hạng Thị trường",
        "outlook": "Rất khả quan - Thanh khoản thị trường bùng nổ & Hệ thống KRX",
        "benchmark_pe": 12.5,
        "benchmark_pb": 1.45,
        "benchmark_roe": 14.8,
        "drivers": [
            "Triển vọng nâng hạng thị trường chứng khoán Việt Nam lên Nhóm Mới nổi (Emerging Market) theo tiêu chuẩn FTSE Russell.",
            "Vận hành hệ thống giao dịch KRX mở ra nhiều sản phẩm tài chính mới: giao dịch trong ngày (T+0), bán khống có bảo đảm, sản phẩm quyền chọn.",
            "Thanh khoản bình quân toàn thị trường phục hồi mạnh mẽ đạt 20,000 - 30,000 tỷ VNĐ/phiên.",
            "Dư nợ cho vay giao dịch ký quỹ (Margin) tăng trưởng lập kỷ lục mới với biên lãi ổn định."
        ],
        "risks": [
            "Biến động danh mục tự doanh (FVTPL / AFS) trong các nhịp điều chỉnh bất ngờ của thị trường.",
            "Cạnh tranh hạ phí giao dịch (Zero-fee) giữa các CTCK vốn ngoại làm thu hẹp biên lợi nhuận mảng môi giới thuần."
        ],
        "porter_forces": {
            "threat_of_entry": "Trung bình (Đòi hỏi giấy phép Ủy ban Chứng khoán Nhà nước và quy mô vốn điều lệ tối thiểu cao)",
            "supplier_power": "Thấp (Nguồn vốn vay ngân hàng và phát hành trái phiếu đa dạng)",
            "buyer_power": "Cao (Nhà đầu tư cá nhân có xu hướng chuyển đổi tài khoản theo chính sách phí và lãi suất margin)",
            "substitute_threat": "Thấp (Kênh đầu tư chứng khoán có tính thanh khoản cao nhất trong các kênh tích sản tài chính)",
            "industry_rivalry": "Rất cao (Cuộc đua tăng vốn điều lệ và hạ lãi suất cho vay margin giữa các CTCK nội và ngoại)"
        },
        "peers": [
            {"ticker": "SSI", "name": "Chứng khoán SSI", "market_cap_bil": 37300, "pe": 10.92, "pb": 1.40, "roe": 13.9, "rev_growth": 6.0, "market_share": "Top 2 thị phần môi giới HOSE", "position": "Thương hiệu tài chính định chế số 1"},
            {"ticker": "VND", "name": "VNDIRECT", "market_cap_bil": 22000, "pe": 11.5, "pb": 1.15, "roe": 11.2, "rev_growth": 8.5, "market_share": "Top 3 thị phần môi giới cá nhân", "position": "Nền tảng công nghệ môi giới mạnh"},
            {"ticker": "VCI", "name": "Vietcap", "market_cap_bil": 21500, "pe": 15.2, "pb": 1.85, "roe": 14.0, "rev_growth": 19.0, "market_share": "Dẫn đầu mảng Ngân hàng đầu tư (IB)", "position": "Vua tư vấn M&A và ECM"}
        ]
    },
    "REAL_ESTATE": {
        "name": "Bất động sản Dân dụng",
        "cycle_stage": "Giai đoạn Bắt đầu Hồi phục từ Vùng đáy",
        "outlook": "Trung lập đến Khả quan - Tháo gỡ nút thắt pháp lý dự án",
        "benchmark_pe": 13.5,
        "benchmark_pb": 1.30,
        "benchmark_roe": 12.0,
        "drivers": [
            "Hệ thống ba bộ luật mới (Luật Đất đai, Luật Nhà ở, Luật Kinh doanh BĐS) chính thức có hiệu lực giải tỏa tắc nghẽn pháp lý hàng loạt dự án.",
            "Lãi suất cho vay mua nhà duy trì ở mức hấp dẫn 6.0% - 8.5%/năm giúp kích hoạt lại nhu cầu ở thực.",
            "Các đại dự án vùng ven đô thị lớn và cơ sở hạ tầng giao thông kết nối mở ra nguồn cung mới chất lượng."
        ],
        "risks": [
            "Áp lực thanh toán các lô trái phiếu doanh nghiệp đáo hạn trong năm đối với một số chủ đầu tư đòn bẩy cao.",
            "Tốc độ cấp phép và tính toán tiền sử dụng đất tại các địa phương còn phụ thuộc vào hướng dẫn thi hành."
        ],
        "porter_forces": {
            "threat_of_entry": "Thấp (Yêu cầu quỹ đất sạch tích lũy lâu năm, tiềm lực tài chính lớn và uy tín triển khai dự án)",
            "supplier_power": "Trung bình (Các nhà thầu xây dựng và nhà cung cấp vật liệu chịu sự chi phối của chủ đầu tư uy tín)",
            "buyer_power": "Trung bình (Nhu cầu nhà ở thực tại các đô thị lớn Hà Nội, TP.HCM luôn vượt xa nguồn cung sơ cấp)",
            "substitute_threat": "Rất thấp (Bất động sản gắn liền với thói quen tích sản truyền thống của người Việt Nam)",
            "industry_rivalry": "Trung bình (Sự phân hóa rõ rệt: Chủ đầu tư có pháp lý chuẩn và tài chính lành mạnh chiếm lĩnh thị phần)"
        },
        "peers": [
            {"ticker": "VHM", "name": "Vinhomes", "market_cap_bil": 190000, "pe": 6.8, "pb": 0.98, "roe": 18.5, "rev_growth": 12.0, "market_share": ">25% thị phần căn hộ sơ cấp toàn quốc", "position": "Thống lĩnh thị trường BĐS"},
            {"ticker": "KDH", "name": "Khang Điền", "market_cap_bil": 28000, "pe": 24.5, "pb": 1.80, "roe": 7.5, "rev_growth": 15.0, "market_share": "Thế mạnh khu Đông & Nam TP.HCM", "position": "Pháp lý dự án và tài chính siêu sạch"},
            {"ticker": "NLG", "name": "Nam Long", "market_cap_bil": 15500, "pe": 16.2, "pb": 1.45, "roe": 9.2, "rev_growth": 20.5, "market_share": "Phân khúc nhà ở vừa túi tiền (Affordable)", "position": "Đối tác chiến lược Nhật Bản"}
        ]
    }
}

def get_industry_analysis(sector_code: str) -> Dict[str, Any]:
    """
    Truy xuất báo cáo phân tích ngành, ma trận cạnh tranh và dữ liệu peers.
    """
    return INDUSTRY_DATABASE.get(sector_code, {
        "name": "Chưa phân loại ngành", "cycle_stage": "Chưa có dữ liệu",
        "outlook": "Chưa có dữ liệu ngành đáng tin cậy",
        "benchmark_pe": 0.0, "benchmark_pb": 0.0, "benchmark_roe": 0.0,
        "drivers": [], "risks": [], "porter_forces": {}, "peers": [],
    })

def get_all_industries() -> Dict[str, Dict[str, Any]]:
    """
    Trả về toàn bộ cơ sở dữ liệu các ngành đã chuẩn hóa.
    """
    return INDUSTRY_DATABASE
