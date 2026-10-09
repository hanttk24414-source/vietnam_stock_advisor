"""Explain recommendations from the selected ticker's actual observations."""


def build_recommendation(ticker, technical, fundamental=None, valuation=None,
                         total_score=None, price_status=None):
    fund, val, status = fundamental or {}, valuation or {}, price_status or {}
    price = technical.get('current_price', 0)
    missing = list(fund.get('missing_fields', []))
    complete = (fund.get('available', False) and val.get('available', False)
                and total_score is not None and not missing)
    rsi = technical.get('rsi', 50)
    ma20, ma50 = technical.get('sma20', price), technical.get('sma50', price)
    atr = max(technical.get('atr14', 0), price * .01)
    support_candidates = [x for x in technical.get('support_levels', []) if 0 < x < price]
    support = max(support_candidates) if support_candidates else max(0, price-2*atr)
    resistance_candidates = [x for x in technical.get('resistance_levels', []) if x > price]
    resistance = min(resistance_candidates) if resistance_candidates else price+2*atr
    bullish = price > ma20 > ma50
    bearish = price < ma20 and price < ma50
    volume = technical.get('vol_surge_ratio', 0)
    growth = fund.get('ni_growth_yoy', 0)
    upside = val.get('blended_upside', 0)

    # Identical inputs should produce identical decisions, different facts different explanations.
    insufficient_history = technical.get('observation_count', 200) < 50
    if status.get('stale'):
        rating = 'CHƯA KHUYẾN NGHỊ — GIÁ CHƯA CẬP NHẬT'
        action = f'{ticker}: chờ giá mới; phiên cuối {status.get("price_as_of", "chưa rõ")}.'
    elif not complete or insufficient_history:
        rating = 'CHƯA ĐỦ DỮ LIỆU ĐẦU TƯ'
        action = f'{ticker}: chỉ theo dõi kỹ thuật; chưa đưa giá mục tiêu hoặc khuyến nghị mua khi thiếu BCTC/định giá.'
    elif fund.get('loss_making'):
        rating = 'THEO DÕI / TRUNG LẬP (NEUTRAL)'
        action = f'{ticker}: doanh nghiệp đang lỗ; chưa dùng P/E và cần đánh giá khả năng phục hồi trước khi mua mới.'
    elif total_score < 35 or upside <= -10 or (growth < -20 and bearish):
        rating = 'GIẢM TỶ TRỌNG (REDUCE)'
        action = f'{ticker}: hạn chế mua mới; đánh giá lại vị thế khi giá mất hỗ trợ {support:,.0f} đ.'
    elif total_score >= 80 and upside >= 20 and bullish and rsi < 70 and growth > 0:
        rating = 'MUA MẠNH (STRONG BUY)'
        action = f'{ticker}: cân nhắc giải ngân từng phần khi kiểm định hỗ trợ {support:,.0f} đ; tránh mua đuổi.'
    elif total_score >= 65 and upside >= 10 and not bearish and rsi < 70 and growth > 0:
        rating = 'MUA / TÍCH LŨY (ACCUMULATE)'
        action = f'{ticker}: cân nhắc tích lũy gần hỗ trợ {support:,.0f} đ; cần giữ trên MA20 {ma20:,.0f} đ.'
    elif total_score >= 50 and upside > 0 and not bearish:
        rating = 'NẮM GIỮ (HOLD)'
        action = f'{ticker}: theo dõi vị thế hiện tại và phản ứng tại kháng cự {resistance:,.0f} đ.'
    else:
        rating = 'THEO DÕI / TRUNG LẬP (NEUTRAL)'
        action = f'{ticker}: chờ giá vượt MA20 {ma20:,.0f} đ và cải thiện lợi nhuận/định giá trước khi mua mới.'
    if rsi >= 70 and complete and not status.get('stale'):
        action += f' RSI {rsi:.1f} đang quá mua, cần chờ hạ nhiệt.'

    trend = 'tăng' if bullish else ('giảm' if bearish else 'chưa đồng thuận')
    evidence = [f'{ticker}: giá {price:,.0f} đ, MA20 {ma20:,.0f} đ, MA50 {ma50:,.0f} đ; xu hướng {trend}.',
                f'RSI {rsi:.1f}; MACD histogram {technical.get("macd_hist", 0):,.1f}; khối lượng {volume:.2f} lần trung bình 20 phiên.']
    if fund.get('available'):
        evidence.append(f'BCTC {fund.get("period", "")}: doanh thu {fund.get("rev_growth_yoy", 0):+.1f}%, lợi nhuận {growth:+.1f}%; ROE {fund.get("roe", 0):.1f}%.')
    if val.get('available'):
        evidence.append(f'Giá mục tiêu theo giả định {val["blended_target_price"]:,.0f} đ; chênh lệch {upside:+.1f}% với giá phiên cuối.')
    risks = []
    if insufficient_history:
        risks.append('Chưa đủ 50 phiên; MA50 chưa đủ độ dài quan sát.')
    if not complete:
        risks.append('Thiếu dữ liệu: ' + ', '.join(missing or ['BCTC hoặc cơ sở định giá phù hợp']))
    if rsi >= 70:
        risks.append(f'RSI {rsi:.1f} quá mua; rủi ro mua đuổi.')
    if bearish:
        risks.append(f'Giá dưới MA20 {ma20:,.0f} và MA50 {ma50:,.0f} đ.')
    if volume < .7:
        risks.append(f'Thanh khoản phiên cuối chỉ {volume:.2f} lần trung bình 20 phiên.')
    if fund.get('available') and fund.get('fcf_bil', 0) < 0:
        risks.append(f'Dòng tiền tự do OCF−CapEx âm {fund["fcf_bil"]:,.1f} tỷ đồng.')
    if fund.get('available') and growth < 0:
        risks.append(f'Lợi nhuận giảm {abs(growth):.1f}% trong kỳ so sánh.')
    if val.get('available'):
        risks.append(val.get('assumptions', 'Giá mục tiêu phụ thuộc giả định định giá.'))
    confirmation = f'Giá vượt {max(price, ma20):,.0f} đ, MACD histogram dương và khối lượng ≥1.2 lần trung bình 20 phiên.'
    invalidation = f'Giá đóng cửa dưới hỗ trợ tham chiếu {support:,.0f} đ hoặc BCTC mới làm thay đổi luận điểm.'
    return {'rating': rating, 'action_guide': action, 'summary': ' '.join(evidence),
            'evidence': evidence, 'risks': risks, 'complete': complete,
            'confirmation': confirmation, 'invalidation': invalidation,
            'support': round(support), 'resistance': round(resistance)}
