import requests
from bs4 import BeautifulSoup
import os
import json
from datetime import datetime

# 1. 설정
DISCORD_WEBHOOK_URL = os.environ.get('WHALE_WEBHOOK')
# 🚨 우리 웹사이트 백엔드 주소 (인텔리전스 통합 창고)
SERVER_URL = "https://dividend-server.onrender.com/update_intel"
TEST_MODE = False # 100만 달러 이상만 필터링하려면 False

def convert_value_to_num(val_str):
    """문자열 금액($1.2M 등)을 숫자(float)로 변환"""
    try:
        clean_str = val_str.replace('$', '').replace(',', '').upper().strip()
        multiplier = 1
        if 'M' in clean_str:
            multiplier = 1_000_000
            clean_str = clean_str.replace('M', '')
        elif 'K' in clean_str:
            multiplier = 1_000
            clean_str = clean_str.replace('K', '')
        return float(clean_str) * multiplier
    except:
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
        
        tables = soup.find_all('table', class_='table-light')
        rows = tables[0].find_all('tr') if tables else []
        
        raw_trades = []
        for row in rows[1:20]: 
            cols = row.find_all('td')
            if len(cols) < 9: continue
            
            trade_type = cols[5].text.strip() # 'Buy'
            value_str = cols[8].text.strip()
            value_num = convert_value_to_num(value_str)
            
            # 🚨 필터 조건: 매수(Buy)이면서 100만 달러($1M) 이상
            is_buy = "Buy" in trade_type
            if TEST_MODE or (is_buy and value_num >= 1000000):
                ticker = cols[1].text.strip()
                insider = cols[2].text.strip()
                relationship = cols[3].text.strip()
                price = cols[6].text.strip()
                
                # 우리 서버와 디스코드가 모두 사용할 수 있게 원본 데이터를 딕셔너리로 저장
                raw_trades.append({
                    "type": "WHALE",  # 인텔리전스 타입 구분
                    "symbol": ticker,
                    "owner": insider,
                    "relationship": relationship,
                    "value": f"${value_str}",
                    "price": price,
                    "is_buy": is_buy
                })
        
        return raw_trades
    except Exception as e:
        print(f"❌ 데이터 분석 오류: {e}")
        return []

def send_to_website_server(trade):
    """우리 FastAPI 서버로 전송"""
    try:
        # Render 서버가 깨어나는 시간을 고려해 timeout을 넉넉히 줌
        res = requests.post(SERVER_URL, json=trade, timeout=15)
        if res.status_code == 200:
            print(f"✅ 웹사이트 전송 성공: {trade['symbol']}")
        else:
            print(f"⚠️ 서버 응답 에러: {res.status_code}")
    except Exception as e:
        print(f"❌ 서버 연결 실패 (잠들어 있을 가능성): {e}")

def send_to_discord(trades):
    """디스코드 웹훅 전송"""
    if not DISCORD_WEBHOOK_URL: return

    embeds = []
    for t in trades[:10]:
        embeds.append({
            "title": f"🐋 초대형 고래 포착: {t['symbol']} ({t['value']})",
            "description": f"👤 **{t['owner']}** ({t['relationship']})\n💰 총 거래액: **{t['value']}**\n💵 체결가: ${t['price']}",
            "color": 3066993,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "주린이 계산기 - 고래 추적 시스템"}
        })

    payload = {"embeds": embeds}
    requests.post(DISCORD_WEBHOOK_URL, json=payload)
    print(f"📢 디스코드 알림 전송 완료! ({len(trades)}건)")

def run_whale_tracker():
    print(f"🚀 고래 사냥 시작... ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    trades = get_insider_trades()
    
    if not trades:
        print("✅ 새로운 대형 거래가 없습니다.")
        return

    # 1. 우리 웹사이트 서버로 한 건씩 전송
    for trade in trades:
        send_to_website_server(trade)

    # 2. 디스코드로 통합 전송
    send_to_discord(trades)

if __name__ == "__main__":
    run_whale_tracker()
