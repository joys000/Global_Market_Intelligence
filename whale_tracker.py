import requests
from bs4 import BeautifulSoup
import os
import json
from datetime import datetime

# 1. 환경 설정 (수정 금지)
DISCORD_WEBHOOK_URL = os.environ.get('WHALE_WEBHOOK')
# 🚨 렌더 서버의 인텔리전스 통합 창고 주소
SERVER_URL = "https://dividend-server.onrender.com/update_intel"
TEST_MODE = False # True로 바꾸면 100만 달러 미만도 수집함 (테스트용)

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
    """핀비즈에서 최신 내부자 거래 데이터를 긁어옴"""
    url = "https://finviz.com/insidertrading.ashx"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://finviz.com/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 핀비즈 테이블 구조 파악
        tables = soup.find_all('table', class_='table-light')
        rows = tables[0].find_all('tr') if tables else []
        
        raw_trades = []
        for row in rows[1:25]: # 상위 25개 필터링
            cols = row.find_all('td')
            if len(cols) < 9: continue
            
            trade_type = cols[5].text.strip() # 'Buy'
            value_str = cols[8].text.strip()
            value_num = convert_value_to_num(value_str)
            
            # 🚨 멘토의 필터링 조건: 오직 'Buy(매수)' 이면서 '$1,000,000(13억)' 이상만!
            is_buy = "Buy" in trade_type
            if TEST_MODE or (is_buy and value_num >= 1000000):
                ticker = cols[1].text.strip()
                insider = cols[2].text.strip()
                relationship = cols[3].text.strip()
                price = cols[6].text.strip()
                date = cols[0].text.strip() # 거래 발생일
                
                raw_trades.append({
                    "type": "WHALE",  # 우리 웹사이트가 고래 뱃지를 달아주기 위한 식별자
                    "symbol": ticker,
                    "owner": insider,
                    "relationship": relationship,
                    "value": f"${value_str}",
                    "price": price,
                    "date": date,
                    "is_buy": is_buy
                })
        
        return raw_trades
    except Exception as e:
        print(f"❌ 데이터 분석 오류: {e}")
        return []

def send_to_website_server(trade):
    """우리 렌더 백엔드 서버(FastAPI) 창고로 데이터 전송"""
    try:
        # Render 무료 서버의 부팅 시간을 고려해 타임아웃 15초 부여
        res = requests.post(SERVER_URL, json=trade, timeout=15)
        if res.status_code == 200:
            print(f"✅ 웹사이트 전송 성공: {trade['symbol']}")
        else:
            print(f"⚠️ 서버 응답 에러({res.status_code}): {trade['symbol']}")
    except Exception as e:
        print(f"❌ 서버 연결 실패 (서버가 자고 있거나 주소가 틀림): {e}")

def send_to_discord(trades):
    """디스코드 채널 알림 전송"""
    if not DISCORD_WEBHOOK_URL or not trades: return

    embeds = []
    for t in trades[:10]: # 한 번에 최대 10개만 보냄
        embeds.append({
            "title": f"🐋 초대형 고래 포착: {t['symbol']} ({t['value']})",
            "description": f"👤 **{t['owner']}** ({t['relationship']})\n💰 총 거래액: **{t['value']}**\n💵 체결가: ${t['price']}\n📅 거래일: {t['date']}",
            "color": 3066993, # 초록색
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "주린이 인텔리전스 - 세력 추적기"}
        })

    payload = {"embeds": embeds}
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        print(f"📢 디스코드 알림 전송 완료! ({len(trades)}건)")
    except Exception as e:
        print(f"❌ 디스코드 전송 실패: {e}")

def run_whale_tracker():
    print(f"🚀 고래 사냥 시작... {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    trades = get_insider_trades()
    
    if not trades:
        print("🔍 조건($1M 이상 매수)에 맞는 거래가 없습니다.")
        return

    # 1. 렌더 서버로 데이터 전송 (웹사이트 노출용)
    for trade in trades:
        send_to_website_server(trade)

    # 2. 디스코드로 데이터 전송 (알림용)
    send_to_discord(trades)

if __name__ == "__main__":
    run_whale_tracker()
