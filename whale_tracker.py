import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

# 설정: 고래 알림 전용 웹훅 (GitHub Secrets에 등록 필수)
DISCORD_WEBHOOK_URL = os.environ.get('WHALE_WEBHOOK')

def get_insider_trades():
    # OpenInsider: 최근 2.5만 달러 이상의 내부자 매수 기록 페이지
    url = "http://openinsider.com/insider-transactions-25k"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 데이터 테이블 찾기
        table = soup.find('table', class_='tinytable')
        if not table: return []
        
        rows = table.find_all('tr')[1:11] # 최신 10건 확인
        trades = []
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 10: continue
            
            # 'P - Purchase' (직접 매수)인 경우만 필터링
            trade_type = cols[7].text.strip()
            if "P - Purchase" in trade_type:
                ticker = cols[3].text.strip()
                insider = cols[4].text.strip()
                title = cols[5].text.strip()
                price = cols[8].text.strip()
                value = cols[10].text.strip()
                
                trades.append({
                    "ticker": ticker,
                    "info": f"👤 **{insider}** ({title})\n💰 거래규모: **{value}**\n💵 매수가: {price}"
                })
        return trades
    except Exception as e:
        print(f"❌ 데이터 추출 오류: {e}")
        return []

def send_to_discord():
    if not DISCORD_WEBHOOK_URL:
        print("❌ 에러: WHALE_WEBHOOK 설정이 누락되었습니다.")
        return

    trades = get_insider_trades()
    if not trades:
        print("✅ 새로 포착된 대량 매수 건이 없습니다.")
        return

    embeds = []
    for trade in trades:
        embeds.append({
            "title": f"🚀 내부자 대량 매수 포착: {trade['ticker']}",
            "description": trade['info'],
            "color": 3066993, # 신뢰의 초록색
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "주린이 계산기 - 세력 추적 시스템"}
        })

    # 디스코드는 한 번에 최대 10개 임베드 전송 가능
    payload = {"embeds": embeds[:10]}
    requests.post(DISCORD_WEBHOOK_URL, json=payload)
    print(f"✅ {len(embeds)}건의 고래 알림 전송 완료!")

if __name__ == "__main__":
    send_to_discord()
