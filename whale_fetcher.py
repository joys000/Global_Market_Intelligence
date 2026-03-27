import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

# 1. 렌더 서버 주소
SERVER_URL = "https://dividend-server.onrender.com/update_intel"

# 2. 고래들이 모이는 곳 (100만 달러 이상 매수 필터)
WHALE_URL = "http://openinsider.com/screener?s=&o=&pl=&ph=&ll=&lh=&fd=3&fdr=&td=0&tdr=&fdy=&tdy=&v=1000&max_v=&mcl=&mch=&is=&isc=&ia=&iac=&it%5B%5D=p&it%5B%5D=pp&sort_col=0&sort_dir=0&record_cnt=10"

def get_whale_data():
    print(f"🌊 고래 사냥 시작... {datetime.now().strftime('%H:%M:%S')}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # --- 🎣 1단계: 끈기 있게 그물 던지기 (Retry 로직) ---
    success = False
    for attempt in range(3):
        try:
            print(f"🎣 {attempt + 1}번째 그물 던지는 중...")
            res = requests.get(WHALE_URL, headers=headers, timeout=60)
            
            if res.status_code == 200:
                print("✨ 사이트 접속 성공! 데이터 분석 시작...")
                soup = BeautifulSoup(res.text, 'html.parser')
                
                # --- 🔪 2단계: 물고기 손질하기 (데이터 추출) ---
                rows = soup.find_all('tr')[1:]  # 헤더 제외
                
                if not rows:
                    print("⚠️ 잡힌 물고기가 없습니다. (조건에 맞는 데이터 없음)")
                    return

                for row in rows[:5]:  # 최신 5건만
                    cols = row.find_all('td')
                    if len(cols) < 11: continue
                    
                    ticker = cols[3].text.strip()
                    insider_name = cols[4].text.strip()
                    title = cols[5].text.strip()
                    price = cols[8].text.strip()
                    quantity = cols[9].text.strip()
                    value = cols[10].text.strip()

                    display_title = f"🐋 [내부자 매수] {ticker} ({insider_name})"
                    display_content = f"{title}가 {price} 달러에 {quantity}주 매수! (총액: {value})"
                    link = f"https://finviz.com/quote.ashx?t={ticker}"
                    
                    news_data = {
                        "type": "WHALE",
                        "source": "OpenInsider",
                        "symbol": ticker,
                        "title": f"{display_title}: {display_content}",
                        "link": link,
                        "timestamp": datetime.now().strftime("%H:%M")
                    }
                    
                    # --- 📤 3단계: 창고로 배송 (서버 전송) ---
                    try:
                        send_res = requests.post(SERVER_URL, json=news_data, timeout=30)
                        if send_res.status_code == 200:
                            print(f"✅ 고래 입고 완료: {ticker} ({value})")
                    except Exception as e:
                        print(f"❌ 서버 전송 실패: {e}")
                
                success = True
                break  # 모든 작업 성공 시 루프 탈출
                
        except Exception as e:
            print(f"⚠️ {attempt + 1}번째 시도 에러: {e}")
            if attempt < 2:
                print("⏳ 5초 뒤에 다시 던집니다...")
                time.sleep(5)
            else:
                print("❌ 결국 사냥에 실패했습니다.")

if __name__ == "__main__":
    get_whale_data()
