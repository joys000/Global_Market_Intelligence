import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

# 1. 렌더 서버 주소 (중앙 통제실)
SERVER_URL = "https://dividend-server.onrender.com/update_intel"

# 2. 고래들이 모이는 곳 (OpenInsider - 100만 달러 이상 매수 필터)
WHALE_URL = "http://openinsider.com/screener?s=&o=&pl=&ph=&ll=&lh=&fd=3&fdr=&td=0&tdr=&fdy=&tdy=&v=1000&max_v=&mcl=&mch=&is=&isc=&ia=&iac=&it%5B%5D=p&it%5B%5D=pp&sort_col=0&sort_dir=0&record_cnt=10"

def get_whale_data():
    print(f"🌊 고래 사냥 시작... {datetime.now().strftime('%H:%M:%S')}")
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(WHALE_URL, headers=headers, timeout=20)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 테이블에서 데이터 행 추출
        rows = soup.find_all('tr')[1:] # 헤더 제외
        
        for row in rows[:5]: # 최신 5건만 처리
            cols = row.find_all('td')
            if len(cols) < 10: continue
            
            ticker = cols[3].text.strip()       # 티커 (예: TSLA)
            insider_name = cols[4].text.strip() # 이름
            title = cols[5].text.strip()        # 직함 (CEO, Director 등)
            trade_type = cols[7].text.strip()   # 거래 종류 (Purchase)
            price = cols[8].text.strip()        # 매수가
            quantity = cols[9].text.strip()     # 수량
            value = cols[10].text.strip()       # 총 금액 (예: +$1,200,000)

            # --- 🇰🇷 한글 메시지로 가공 ---
            # 민주가 관심 있는 DUOL이나 NVDY가 뜨면 더 대박이겠지?
            display_title = f"🐋 [내부자 매수] {ticker} ({insider_name})"
            display_content = f"{title}가 {price} 달러에 {quantity}주 매수! (총액: {value})"
            
            link = f"https://finviz.com/quote.ashx?t={ticker}" # 상세 정보 링크
            
            news_data = {
                "type": "WHALE",
                "source": "OpenInsider",
                "symbol": ticker,
                "title": f"{display_title}: {display_content}",
                "link": link,
                "timestamp": datetime.now().strftime("%H:%M")
            }
            
            # --- 📤 서버 전송 ---
            send_res = requests.post(SERVER_URL, json=news_data, timeout=30)
            if send_res.status_code == 200:
                print(f"✅ 고래 입고 완료: {ticker} ({value})")
                
    except Exception as e:
        print(f"❌ 고래 사냥 실패: {e}")

if __name__ == "__main__":
    get_whale_data()