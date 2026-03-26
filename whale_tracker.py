import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

# 1. 설정
DISCORD_WEBHOOK_URL = os.environ.get('WHALE_WEBHOOK')
SERVER_URL = "https://dividend-server.onrender.com/update_intel"
# 🚨 테스트 완료! 다시 진짜 고래 사냥 모드로 전환
TEST_MODE = False 

def convert_value_to_num(val_str):
    try:
        clean_str = val_str.replace('$', '').replace(',', '').upper().strip()
        multiplier = 1
        if 'M' in clean_str: multiplier = 1_000_000; clean_str = clean_str.replace('M', '')
        elif 'K' in clean_str: multiplier = 1_000; clean_str = clean_str.replace('K', '')
        return float(clean_str) * multiplier
    except: return 0

def get_insider_trades():
    url = "https://finviz.com/insidertrading.ashx"
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36", "Referer": "https://finviz.com/"}
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = [tr for tr in soup.find_all('tr') if len(tr.find_all('td')) >= 9]
        
        raw_trades = []
        for row in rows[1:15]: # 상위 15개 검사
            cols = row.find_all('td')
            # 🚨 컬럼 인덱스 수정 (핀비즈 표준 구조)
            ticker = cols[0].text.strip()       # Index 0: Ticker
            owner = cols[1].text.strip()        # Index 1: Owner
            relationship = cols[2].text.strip() # Index 2: Relationship
            date_str = cols[3].text.strip()     # Index 3: Date
            trade_type = cols[4].text.strip()   # Index 4: Transaction (Buy/Sale)
            price = cols[5].text.strip()        # Index 5: Cost
            value_str = cols[7].text.strip()    # Index 7: Value
            
            value_num = convert_value_to_num(value_str)
            is_buy = "Buy" in trade_type

            # 🚨 최종 필터: 매수이면서 100만 달러 이상 (혹은 테스트모드)
            if TEST_MODE or (is_buy and value_num >= 1000000):
                raw_trades.append({
                    "type": "WHALE",
                    "symbol": ticker,
                    "owner": owner,
                    "relationship": relationship,
                    "value": f"${value_str}",
                    "price": price,
                    "date": date_str,
                    "is_buy": is_buy
                })
        return raw_trades
    except Exception as e:
        print(f"❌ 분석 오류: {e}"); return []

def send_to_website_server(trade):
    try:
        res = requests.post(SERVER_URL, json=trade, timeout=15)
        print(f"✅ 서버 전송 결과 ({trade['symbol']}): {res.status_code}")
    except Exception as e:
        print(f"❌ 서버 연결 실패: {e}")

if __name__ == "__main__":
    print(f"🚀 고래 사냥 시작... {datetime.now()}")
    trades = get_insider_trades()
    if not trades:
        print("🔍 현재 조건에 맞는 대형 고래가 없습니다.")
    else:
        for trade in trades:
            send_to_website_server(trade)
