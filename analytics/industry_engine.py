"""
Module phân tích chuyên sâu ngành và định vị cạnh tranh doanh nghiệp.
Phân tích:
1. Chu kỳ ngành, động lực tăng trưởng và rủi ro.
2. Ma trận 5 áp lực cạnh tranh của Michael Porter (Porter's Five Forces).
3. So sánh tương quan vị thế doanh nghiệp với trung bình ngành và nhóm cổ phiếu cùng ngành (Peers).
"""

from typing import Dict, Any, List
from data.industry_loader import get_industry_analysis

def evaluate_industry_and_peers(sector_code: str, stock_fundamentals: Dict[str, Any]) -> Dict[str, Any]:
    """
    Đánh giá ngành và so sánh cổ phiếu mục tiêu với các đối thủ cạnh tranh.
    """
    industry_info = get_industry_analysis(sector_code)
    
    ticker = stock_fundamentals.get("ticker", "HPG")
    stock_pe = stock_fundamentals.get("pe", 0.0)
    stock_pb = stock_fundamentals.get("pb", 0.0)
    stock_roe = stock_fundamentals.get("roe", 0.0)
    stock_growth = stock_fundamentals.get("rev_growth_yoy", 0.0)
    
    bench_pe = industry_info.get("benchmark_pe", 12.0)
    bench_pb = industry_info.get("benchmark_pb", 1.5)
    bench_roe = industry_info.get("benchmark_roe", 15.0)
    
    # 1. So sánh với chuẩn ngành
    pe_discount = round(((bench_pe - stock_pe) / bench_pe) * 100, 1) if bench_pe > 0 else 0.0
    pb_discount = round(((bench_pb - stock_pb) / bench_pb) * 100, 1) if bench_pb > 0 else 0.0
    roe_premium = round(stock_roe - bench_roe, 1)
    
    # 2. Đánh giá vị thế cạnh tranh
    if stock_roe > bench_roe and stock_pe < bench_pe:
        competitive_moat = "CON HÀO KINH TẾ RỘNG (WIDE MOAT) - HIỆU QUẢ CAO KÈM ĐỊNH GIÁ CHIẾT KHẤU"
        moat_score = 90
    elif stock_roe > bench_roe:
        competitive_moat = "VỊ THẾ DẪN ĐẦU CHẤT LƯỢNG CAO (NARROW MOAT)"
        moat_score = 80
    elif stock_pe < bench_pe:
        competitive_moat = "CỔ PHIẾU GIÁ TRỊ - ĐỊNH GIÁ THẤP HƠN TRUNG BÌNH NGÀNH"
        moat_score = 70
    else:
        competitive_moat = "VỊ THẾ TRUNG BÌNH TRONG NGÀNH"
        moat_score = 60

    # 3. Tổng hợp bảng so sánh Peers
    peers_list: List[Dict[str, Any]] = industry_info.get("peers", [])
    
    return {
        "sector_name": industry_info.get("name"),
        "cycle_stage": industry_info.get("cycle_stage"),
        "outlook": industry_info.get("outlook"),
        "benchmark_pe": bench_pe,
        "benchmark_pb": bench_pb,
        "benchmark_roe": bench_roe,
        "pe_discount_pct": pe_discount,
        "pb_discount_pct": pb_discount,
        "roe_premium_pct": roe_premium,
        "competitive_moat": competitive_moat,
        "moat_score": moat_score,
        "drivers": industry_info.get("drivers", []),
        "risks": industry_info.get("risks", []),
        "porter_forces": industry_info.get("porter_forces", {}),
        "peers": peers_list
    }
