import requests
from bs4 import BeautifulSoup
import os
import json
from datetime import datetime

# 1. 설정
DISCORD_WEBHOOK_URL = os.environ.get('WHALE_WEBHOOK')
SERVER_URL = "https://dividend-server.onrender.com/update_intel"
# 🚨 멘토 지시: 강제 테스트 모드 가동! (모든 거래 수집)
TEST_MODE = True 

def get_insider_trades():
    url = "https://finviz.com/insidertrading.ashx"
    # 🚨 더 강력한 브라우저 흉내 (핀비즈 차단 회피용)
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://finviz.com/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        print(f"📡 핀비즈 응답 상태 코드: {response.status_code}") # 200이 나와야 성공
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 핀비즈는 테이블 구조가 자주 바뀔 수 있으므로 더 유연하게 찾음
        rows = soup.find_all('tr', class_=['table-light-row-cp', 'table-dark-row-cp'])
        
        # 🚨 [디버깅] 줄이 몇 개나 잡히는지 확인
        print(f"🔍 발견된 거래 내역 수: {len(rows)}개")

        if not rows:
            # 만약 class로 안 잡히면 모든 tr을 뒤져서 데이터가 있는지 확인
            rows = [tr for tr in soup.find_all('tr') if len(tr.find_all('td')) >= 9]
            print(f"🔄 백업 로직으로 발견된 내역 수: {len(rows)}개")

        raw_trades = []
        for row in rows[1:10]: # 테스트를 위해 상위 10개만
            cols = row.find_all('td')
            ticker = cols[1].text.strip()
            trade_type = cols[5].text.strip() # 'Buy' or 'Sale'
            value_str = cols[8].text.strip()
            
            # TEST_MODE가 True면 Buy/Sale 상관없이 일단 다 담음
            raw_trades.append({
                "type": "WHALE",
                "symbol": ticker,
                "owner": cols[2].text.strip(),
                "relationship": cols[3].text.strip(),
                "value": f"${value_str}",
                "price": cols[6].text.strip(),
                "date": cols[0].text.strip(),
                "is_buy": "Buy" in trade_type
            })
        
        return raw_trades
    except Exception as e:
        print(f"❌ 데이터 분석 오류: {e}")
        return []

def send_to_website_server(trade):
    try:
        res = requests.post(SERVER_URL, json=trade, timeout=15)
        print(f"✅ 서버 전송 결과 ({trade['symbol']}): {res.status_code}")
    except Exception as e:
        print(f"❌ 서버 연결 실패: {e}")

def run_whale_tracker():
    print(f"🚀 [디버그 모드] 고래 사냥 시작... {datetime.now()}")
    trades = get_insider_trades()
    
    if not trades:
        print("💀 [절망] 사이트에서 데이터를 한 줄도 못 읽어왔습니다. 차단됐거나 구조가 바뀐 듯?")
        return

    print(f"🎯 처리할 거래 건수: {len(trades)}건")
    for trade in trades:
        send_to_website_server(trade)

if __name__ == "__main__":
    run_whale_tracker()
