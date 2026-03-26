import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

# 1. 설정
DISCORD_WEBHOOK_URL = os.environ.get('WHALE_WEBHOOK')
TEST_MODE = False # 100만 달러 이상만 보고 싶다면 False로 설정하세요.

def convert_value_to_num(val_str):
    """문자열 형태의 금액($1,234,567 또는 $1.2M)을 숫자(float)로 변환"""
    try:
        # '$', ',' 제거 및 공백 제거
        clean_str = val_str.replace('$', '').replace(',', '').upper().strip()
        
        multiplier = 1
        if 'M' in clean_str:
            multiplier = 1_000_000
            clean_str = clean_str.replace('M', '')
        elif 'K' in clean_str:
            multiplier = 1_000
            clean_str = clean_str.replace('K', '')
            
        return float(clean_str) * multiplier
    except (ValueError, AttributeError):
        return 0

def get_insider_trades():
    url = "https://finviz.com/insidertrading.ashx"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://finviz.com/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 데이터가 있는 테이블 찾기
        tables = soup.find_all('table', class_='table-light')
        rows = tables[0].find_all('tr') if tables else [tr for tr in soup.find_all('tr') if len(tr.find_all('td')) >= 9]
        
        trades = []
        for row in rows[1:20]: # 상위 20개 행 검사
            cols = row.find_all('td')
            if len(cols) < 9: continue
            
            trade_type = cols[5].text.strip() # 'Buy' 또는 'Sale'
            value_str = cols[8].text.strip()
            value_num = convert_value_to_num(value_str)
            
            # 조건: 'Buy'이면서 1,000,000 달러 이상인 경우
            # (TEST_MODE=True일 때는 모든 거래 수집)
            is_buy = "Buy" in trade_type
            if TEST_MODE or (is_buy and value_num >= 1000000):
                ticker = cols[1].text.strip()
                insider = cols[2].text.strip()
                relationship = cols[3].text.strip()
                price = cols[6].text.strip()
                
                status_text = "🚀 [대형 매수 포착]" if is_buy else "📉 [기타 거래]"
                color = 3066993 if is_buy else 15105570
                
                trades.append({
                    "title": f"{status_text} {ticker} (${value_str})",
                    "description": f"👤 **{insider}** ({relationship})\n💰 총 거래액: **${value_str}**\n💵 체결가: ${price}",
                    "color": color
                })
        
        return trades
    except Exception as e:
        print(f"❌ 데이터 분석 오류: {e}")
        return []

def send_to_discord():
    if not DISCORD_WEBHOOK_URL:
        print("❌ WHALE_WEBHOOK 설정 누락")
        return

    trades = get_insider_trades()
    if not trades:
        print("✅ 100만 달러 이상의 새로운 매수 건이 없습니다.")
        return

    payload = {
        "embeds": [
            {
                "title": t["title"],
                "description": t["description"],
                "color": t["color"],
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {"text": "주린이 계산기 - 고래(1M+) 추적 시스템"}
            } for t in trades[:10]
        ]
    }
    
    requests.post(DISCORD_WEBHOOK_URL, json=payload)
    print(f"✅ {len(trades)}건의 대형 거래 알림 전송 완료!")

if __name__ == "__main__":
    send_to_discord()
