import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

# 1. 설정
DISCORD_WEBHOOK_URL = os.environ.get('WHALE_WEBHOOK')
TEST_MODE = True # 성공 확인을 위해 True 유지

def get_insider_trades():
    # 404 에러를 피하기 위한 최신 경로 (HTTPS 권장)
    url = "https://openinsider.com/latest-insider-trades"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    }
    
    try:
        # 세션을 사용하여 연결 안정성 확보
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=20)
        response.raise_for_status() 
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 'Ticker'라는 텍스트가 포함된 테이블을 더 정밀하게 찾기
        table = None
        for t in soup.find_all('table'):
            header_text = t.find('tr').text if t.find('tr') else ""
            if 'Ticker' in header_text:
                table = t
                break
        
        if not table:
            print("⚠️ 테이블 구조가 변경되었거나 접근이 차단되었습니다.")
            return []
        
        rows = table.find_all('tr')
        trades = []
        
        # 상위 10개 데이터 행 파싱 (헤더 제외)
        for row in rows[1:11]: 
            cols = row.find_all('td')
            if len(cols) < 10: continue
            
            # 데이터 추출
            trade_type = cols[7].text.strip()
            ticker = cols[3].text.strip().split('\n')[0] # 티커만 깔끔하게
            insider = cols[4].text.strip()
            title = cols[5].text.strip()
            price = cols[8].text.strip()
            value = cols[10].text.strip()
            
            # 필터링: 테스트 모드 혹은 매수(Purchase)
            is_purchase = "P - Purchase" in trade_type
            if TEST_MODE or is_purchase:
                trades.append({
                    "title": f"{'🚀 [매수]' if is_purchase else '📉 [매도/기타]'} 포착: {ticker}",
                    "description": f"👤 **{insider}** ({title})\n💰 규모: **{value}**\n💵 가격: {price}",
                    "color": 3066993 if is_purchase else 15105570
                })
                
        return trades

    except requests.exceptions.HTTPError as e:
        print(f"❌ 접속 오류 (주소 확인 필요): {e}")
    except Exception as e:
        print(f"❌ 알 수 없는 오류: {e}")
    return []

def send_to_discord():
    if not DISCORD_WEBHOOK_URL:
        print("❌ WHALE_WEBHOOK 시크릿이 설정되지 않았습니다.")
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
                "footer": {"text": "주린이 계산기 - 세력 실시간 감시"}
            } for t in trades[:5]
        ]
    }
    
    requests.post(DISCORD_WEBHOOK_URL, json=payload)
    print(f"✅ {len(trades)}건 전송 시도 성공!")

if __name__ == "__main__":
    send_to_discord()
