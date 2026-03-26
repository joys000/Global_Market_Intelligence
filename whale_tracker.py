import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

# 1. 설정
DISCORD_WEBHOOK_URL = os.environ.get('WHALE_WEBHOOK')
TEST_MODE = True # 일단 지금은 성공 여부를 확인해야 하니 True로 두세요!

def get_insider_trades():
    url = "http://openinsider.com/insider-transactions-25k"
    
    # 봇이 아니라 실제 '크롬 브라우저'인 척 속이는 더 강력한 헤더
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() # 접속 실패 시 에러 발생
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # [구조 변경 대응] 특정 클래스명이 없어도 'Ticker' 글자가 있는 테이블을 찾음
        table = None
        all_tables = soup.find_all('table')
        for t in all_tables:
            if 'Ticker' in t.text:
                table = t
                break
        
        if not table:
            print("⚠️ 여전히 테이블을 찾을 수 없습니다. (사이트가 접근을 완전히 막았을 가능성)")
            return []
        
        rows = table.find_all('tr')
        trades = []
        
        # 데이터는 보통 2번째 줄(index 1)부터 시작
        for row in rows[1:11]: 
            cols = row.find_all('td')
            if len(cols) < 10: continue
            
            trade_type = cols[7].text.strip()
            
            # 테스트 모드이거나 매수(Purchase)일 때만 수집
            if TEST_MODE or ("P - Purchase" in trade_type):
                ticker = cols[3].text.strip().replace('\x1b', '') # 이상한 문자 제거
                insider = cols[4].text.strip()
                title = cols[5].text.strip()
                price = cols[8].text.strip()
                value = cols[10].text.strip()
                
                is_p = "P - Purchase" in trade_type
                trades.append({
                    "title": f"{'🚀 [매수]' if is_p else '📉 [매도/기타]'} 포착: {ticker}",
                    "description": f"👤 **{insider}** ({title})\n💰 규모: **{value}**\n💵 가격: {price}",
                    "color": 3066993 if is_p else 15105570
                })
                
        return trades
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return []

def send_to_discord():
    if not DISCORD_WEBHOOK_URL:
        print("❌ WHALE_WEBHOOK 설정 누락")
        return

    trades = get_insider_trades()
    if not trades:
        print("✅ 현재 조건에 맞는 데이터가 없습니다.")
        return

    payload = {
        "embeds": [
            {
                "title": t["title"],
                "description": t["description"],
                "color": t["color"],
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {"text": "주린이 계산기 - 세력 실시간 감시"}
            } for t in trades[:5] # 너무 많으면 5개만 전송
        ]
    }
    
    requests.post(DISCORD_WEBHOOK_URL, json=payload)
    print(f"✅ {len(trades)}건 전송 시도 완료!")

if __name__ == "__main__":
    send_to_discord()
