import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

# 1. 렌더 서버 주소
SERVER_URL = "https://dividend-server.onrender.com/update_intel"

# 2. 새로운 사냥터 (Finviz - 최신 내부자 거래 페이지)
# 이 주소는 'Buy' 거래 위주로 보여주는 페이지야.
WHALE_URL = "https://finviz.com/insidertrading.ashx?tc=1"

def get_whale_data():
    print(f"🌊 새로운 사냥터(Finviz) 출동... {datetime.now().strftime('%H:%M:%S')}", flush=True)
    
    # Finviz는 보안이 강력해서 브라우저인 척을 더 잘해야 해!
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    
    for attempt in range(3):
        try:
            print(f"🎣 {attempt + 1}번째 그물 던지는 중 (Finviz)...", flush=True)
            # Finviz는 https를 권장해!
            res = requests.get(WHALE_URL, headers=headers, timeout=30)
            
            if res.status_code == 200:
                print("✨ Finviz 접속 성공! 대물 분석 시작...", flush=True)
                soup = BeautifulSoup(res.text, 'html.parser')
                
                # Finviz의 내부자 거래 테이블 찾기
                # 테이블 행(tr) 중 데이터가 들어있는 것들을 골라내자
                rows = soup.select('table.styled-table-w-full tr')[1:] # 헤더 제외
                
                if not rows:
                    print("⚠️ 오늘따라 고래들이 조용하네? (데이터 없음)", flush=True)
                    return

                count = 0
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) < 9: continue
                    
                    # Finviz 컬럼 구조:
                    # 1:Ticker, 2:Owner, 3:Relationship, 4:Date, 5:Transaction, 6:Cost, 7:#Shares, 8:Value($)
                    ticker = cols[1].text.strip()
                    owner = cols[2].text.strip()
                    relationship = cols[3].text.strip()
                    transaction = cols[5].text.strip() # "Option Exercise"는 거르고 "Buy"만!
                    value = cols[8].text.strip()
                    
                    # 진짜 매수(Buy)만 입고시키자!
                    if "Buy" in transaction:
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
                        
                        # 서버 입고
                        try:
                            requests.post(SERVER_URL, json=news_data, timeout=10)
                            print(f"✅ 입고 완료: {ticker} ({value})", flush=True)
                        except: pass
                        
                        count += 1
                        if count >= 5: break # 너무 많으면 힘드니까 5개만!
                
                print(f"🎊 총 {count}마리의 고래를 창고에 넣었어!", flush=True)
                break
            else:
                print(f"⚠️ 접속 실패 (상태 코드: {res.status_code})", flush=True)
                
        except Exception as e:
            print(f"❌ 에러 발생: {e}", flush=True)
            time.sleep(5)

if __name__ == "__main__":
    get_whale_data()
