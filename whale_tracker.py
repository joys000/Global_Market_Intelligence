import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

# 1. 설정: GitHub Secrets에 등록한 웹훅 주소
DISCORD_WEBHOOK_URL = os.environ.get('WHALE_WEBHOOK')

# 2. 테스트 모드 설정 (True로 바꾸면 매도 기록도 다 가져와서 디스코드로 쏩니다)
TEST_MODE = False 

def get_insider_trades():
    url = "http://openinsider.com/insider-transactions-25k"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', class_='tinytable')
        
        if not table: 
            print("❌ 테이블을 찾을 수 없습니다. 사이트 구조 변경 의심.")
            return []
        
        rows = table.find_all('tr')[1:11] # 최신 10건 검사
        trades = []
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 10: continue
            
            trade_type = cols[7].text.strip()
            
            # [필터링 로직] TEST_MODE가 꺼져있으면 'Purchase'만, 켜져있으면 전부 다!
            if TEST_MODE or ("P - Purchase" in trade_type):
                ticker = cols[3].text.strip()
                insider = cols[4].text.strip()
                title = cols[5].text.strip()
                price = cols[8].text.strip()
                value = cols[10].text.strip()
                
                # 매수면 초록색(3066993), 매도면 주황색(15105570)
                is_purchase = "P - Purchase" in trade_type
                color = 3066993 if is_purchase else 15105570
                status_text = "🚀 [내부자 매수]" if is_purchase else "📉 [내부자 매도(테스트)]"
                
                trades.append({
                    "title": f"{status_text} 포착: {ticker}",
                    "description": f"👤 **{insider}** ({title})\n💰 거래규모: **{value}**\n💵 가격: {price}",
                    "color": color
                })
        return trades
    except Exception as e:
        print(f"❌ 데이터 로딩 중 에러 발생: {e}")
        return []

def send_to_discord():
    if not DISCORD_WEBHOOK_URL:
        print("❌ 에러: WHALE_WEBHOOK 시크릿 설정이 안 되어 있습니다.")
        return

    trades = get_insider_trades()
    
    if not trades:
        print("✅ 현재 필터링 조건에 맞는 거래가 없습니다. (디스코드 전송 스킵)")
        return

    # 디스코드 전송
    payload = {
        "embeds": [
            {
                "title": t["title"],
                "description": t["description"],
                "color": t["color"],
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {"text": "주린이 계산기 - 고래 추적 시스템"}
            } for t in trades[:10] # 최대 10건만 전송
        ]
    }
    
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if response.status_code == 204 or response.status_code == 200:
        print(f"✅ {len(trades)}건의 데이터를 디스코드로 쐈습니다!")
    else:
        print(f"❌ 디스코드 전송 실패: {response.status_code}")

if __name__ == "__main__":
    send_to_discord()
