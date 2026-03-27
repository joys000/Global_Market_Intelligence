import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

SERVER_URL = "https://dividend-server.onrender.com/update_intel"
# tc=1은 'Buy'만 모아보는 필터야
WHALE_URL = "https://finviz.com/insidertrading.ashx?tc=1"

def get_whale_data():
    print(f"🌊 핀비즈 고래 수색 작전 시작... {datetime.now().strftime('%H:%M:%S')}", flush=True)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    }
    
    try:
        res = requests.get(WHALE_URL, headers=headers, timeout=30)
        if res.status_code != 200:
            print(f"⚠️ 접속 실패: {res.status_code}", flush=True)
            return

        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 🔍 전략 수정: 특정 클래스가 아니라 모든 tr을 다 뒤져서 'Buy'가 들어있는 행을 찾자!
        rows = soup.find_all('tr')
        print(f"👀 총 {len(rows)}개의 데이터 행 발견. 분석 중...", flush=True)

        count = 0
        for row in rows:
            cols = row.find_all('td')
            # 핀비즈 내부자 테이블은 보통 열(td)이 9개 이상이야
            if len(cols) < 9: continue
            
            # 텍스트 추출 (깔끔하게)
            row_text = [c.get_text(strip=True) for c in cols]
            
            # 'Buy'라는 글자가 들어있고, 티커(첫번째 혹은 두번째 열)가 비어있지 않은지 확인
            if "Buy" in row_text:
                try:
                    # 핀비즈 컬럼 인덱스 (가끔 바뀔 수 있으니 주의 깊게 매칭)
                    # 0: 거래일, 1: 티커, 2: 이름, 3: 관계, 4: 거래종류, 5: 가격, 6: 수량, 7: 총액...
                    ticker = row_text[1]
                    owner = row_text[2]
                    relationship = row_text[3]
                    value = row_text[8] # Value ($)
                    
                    if not ticker or ticker == "Ticker": continue # 헤더 방지

                    display_title = f"🐋 [내부자 매수] {ticker} ({owner})"
                    display_content = f"{relationship}가 {value} 달러어치 매수!"
                    link = f"https://finviz.com/quote.ashx?t={ticker}"
                    
                    news_data = {
                        "type": "WHALE",
                        "source": "Finviz",
                        "symbol": ticker,
                        "title": f"{display_title}: {display_content}",
                        "link": link,
                        "timestamp": datetime.now().strftime("%H:%M")
                    }
                    
                    # 서버로 배송
                    resp = requests.post(SERVER_URL, json=news_data, timeout=10)
                    if resp.status_code == 200:
                        print(f"✅ 입고 완료: {ticker} ({value})", flush=True)
                        count += 1
                    
                    if count >= 10: break # 한 번에 최대 10개만!
                except Exception as e:
                    continue # 한 줄 에러나도 다음 줄로!

        if count == 0:
            print("⚠️ 'Buy' 데이터를 찾지 못했어. 구조가 또 바뀌었나?", flush=True)
        else:
            print(f"🎊 성공! 총 {count}마리의 고래를 창고에 넣었어!", flush=True)

    except Exception as e:
        print(f"❌ 에러 발생: {e}", flush=True)

if __name__ == "__main__":
    get_whale_data()
