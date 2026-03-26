import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

# 1. 설정
DISCORD_WEBHOOK_URL = os.environ.get('WHALE_WEBHOOK')
TEST_MODE = True # 성공 확인을 위해 일단 True 유지

def get_insider_trades():
    # 주소를 Finviz로 변경 (최신 내부자 거래 페이지)
    url = "https://finviz.com/insidertrading.ashx"
    
    # 더 사람 같은 헤더 설정 (핀비즈 방어막 돌파용)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://finviz.com/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 핀비즈 특유의 테이블 구조 찾기 (class='table-light' 또는 tr 루프)
        rows = soup.find_all('tr', class_='insider-option-row')
        if not rows:
            # 다른 클래스명인 경우 대비
            rows = soup.select('table.table-light tr')[1:11]
            
        trades = []
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 9: continue
            
            # 핀비즈 데이터 위치 (Ticker: 1, Insider: 2, Relationship: 3, Date: 4, Transaction: 5, Cost: 6, Shares: 7, Value: 8)
            ticker = cols[1].text.strip()
            insider = cols[2].text.strip()
            relationship = cols[3].text.strip()
            trade_type = cols[5].text.strip() # Buy / Sale
            price = cols[6].text.strip()
            value = cols[8].text.strip()
            
            # 'Buy'만 필터링 (TEST_MODE일 땐 전체)
            is_buy = "Buy" in trade_type
            if TEST_MODE or is_buy:
                trades.append({
                    "title": f"{'🚀 [매수]' if is_buy else '📉 [매도/기타]'} 포착: {ticker}",
                    "description": f"👤 **{insider}** ({relationship})\n💰 규모: **${value}**\n💵 가격: ${price}",
                    "color": 3066993 if is_buy else 15105570
                })
        
        return trades

    except Exception as e:
        print(f"❌ 핀비즈 접속 오류: {e}")
        return []

def send_to_discord():
    if not DISCORD_WEBHOOK_URL:
        print("❌ WHALE_WEBHOOK 시크릿 설정 누락")
        return

    trades = get_insider_trades()
    if not trades:
        print("✅ 조건에 맞는 데이터가 없어 전송을 중단합니다.")
        return

    payload = {
        "embeds": [
            {
                "title": t["title"],
                "description": t["description"],
                "color": t["color"],
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {"text": "주린이 계산기 - 세력 추적 (Powered by Finviz)"}
            } for t in trades[:5]
        ]
    }
    
    requests.post(DISCORD_WEBHOOK_URL, json=payload)
    print(f"✅ {len(trades)}건 전송 시도 성공!")

if __name__ == "__main__":
    send_to_discord()
