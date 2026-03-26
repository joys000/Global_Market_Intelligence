import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

# 1. 설정
DISCORD_WEBHOOK_URL = os.environ.get('WHALE_WEBHOOK')
TEST_MODE = True # 성공을 눈으로 봐야 하니 True 유지!

def get_insider_trades():
    url = "https://finviz.com/insidertrading.ashx"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://finviz.com/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # [핵심 수술] 핀비즈의 데이터 테이블은 보통 'table-light' 클래스를 가집니다.
        # 클래스명에 의존하지 않고 두 번째로 나타나는 큰 테이블을 찾는 전략입니다.
        tables = soup.find_all('table', class_='table-light')
        if not tables:
            # 클래스가 없다면 모든 tr 중 td가 9개 이상인 행을 직접 수집
            rows = [tr for tr in soup.find_all('tr') if len(tr.find_all('td')) >= 9]
        else:
            # 가장 큰 테이블의 모든 행을 가져옴
            rows = tables[0].find_all('tr')

        print(f"DEBUG: 총 {len(rows)}개의 행을 발견했습니다.") # 어디서 막히는지 확인용
        
        trades = []
        
        # 헤더 제외하고 데이터 파싱
        for row in rows[1:15]: # 상위 15개 검사
            cols = row.find_all('td')
            if len(cols) < 9: continue
            
            # 데이터 위치 매핑 (핀비즈 표준)
            ticker = cols[1].text.strip()
            insider = cols[2].text.strip()
            relationship = cols[3].text.strip()
            trade_type = cols[5].text.strip() # 'Buy' 또는 'Sale'
            price = cols[6].text.strip()
            value = cols[8].text.strip()
            
            # 필터링 로직
            is_buy = "Buy" in trade_type
            if TEST_MODE or is_buy:
                trades.append({
                    "title": f"{'🚀 [매수]' if is_buy else '📉 [매도/기타]'} 포착: {ticker}",
                    "description": f"👤 **{insider}** ({relationship})\n💰 규모: **${value}**\n💵 가격: ${price}",
                    "color": 3066993 if is_buy else 15105570
                })
        
        return trades

    except Exception as e:
        print(f"❌ 핀비즈 데이터 분석 오류: {e}")
        return []

def send_to_discord():
    if not DISCORD_WEBHOOK_URL:
        print("❌ WHALE_WEBHOOK 설정이 비어있습니다.")
        return

    trades = send_to_discord_logic() # 아래 내부 함수 실행
    
def send_to_discord_logic():
    trades = get_insider_trades()
    
    if not trades:
        print("✅ 조건에 맞는 데이터가 없습니다. (추출된 행이 0개)")
        return

    # 디스코드 임베드 생성
    embeds = []
    for t in trades[:5]: # 너무 많으면 5개만
        embeds.append({
            "title": t["title"],
            "description": t["description"],
            "color": t["color"],
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "주린이 계산기 - 세력 실시간 감시"}
        })

    payload = {"embeds": embeds}
    res = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    
    if res.status_code == 204 or res.status_code == 200:
        print(f"✅ {len(trades)}건의 고래 알림을 디스코드로 쐈습니다!")
    else:
        print(f"❌ 전송 실패 (상태 코드: {res.status_code})")

if __name__ == "__main__":
    send_to_discord_logic()
