import feedparser
import requests
import time
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

# 1. 렌더 서버 주소 (중앙 통제실)
SERVER_URL = "https://dividend-server.onrender.com/update_intel"

# 2. 📡 사냥할 뉴스 창고들
NEWS_SOURCES = {
    "국내경제": "https://www.mk.co.kr/rss/30100041/",
    "해외경제": "https://www.investing.com/rss/news_285.rss",
    "해외속보": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000311"
}

def translate_text(text):
    """영어를 한국어로 번역하는 함수"""
    try:
        return GoogleTranslator(source='en', target='ko').translate(text)
    except:
        return text

def fetch_and_send():
    print(f"🚀 사냥 시작... {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    for category, url in NEWS_SOURCES.items():
        feed = feedparser.parse(url)
        
        # 각 소스당 최신 5개씩만 사냥
        for entry in feed.entries[:5]:
            title = entry.title
            
            # --- 🕒 3. 진짜 뉴스 발행 시간 추출 및 한국 시간(KST) 보정 ---
            if hasattr(entry, 'published_parsed'):
                # RSS의 struct_time을 datetime 객체로 변환 (기본적으로 UTC/GMT 기준인 경우가 많음)
                dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                
                # 해외 소스인 경우 9시간을 더해 한국 시간으로 맞춤 (Investng, CNBC 등)
                if category in ["해외경제", "해외속보"]:
                    dt = dt + timedelta(hours=9)
                
                pub_time = dt.strftime("%H:%M")
            else:
                # 시간이 없을 경우에만 현재 시간 기록
                pub_time = datetime.now().strftime("%H:%M")

            # --- 🌐 4. 해외 소스 번역 ---
            if category in ["해외경제", "해외속보"]:
                print(f"🔄 번역 중: {title[:20]}...")
                title = translate_text(title)

            # --- 📦 5. 서버로 보낼 데이터 뭉치 ---
            news_data = {
                "type": "NEWS",
                "source": category,
                "title": title,
                "link": entry.link,
                "timestamp": pub_time  # 👈 이제 '배송 시간'이 아닌 '진짜 뉴스 시간'!
            }
            
            # --- 📤 6. 서버 전송 ---
            try:
                # 서버가 잠들어 있을 수 있으니 timeout은 넉넉하게 30초
                res = requests.post(SERVER_URL, json=news_data, timeout=30)
                if res.status_code == 200:
                    print(f"✅ 입고 완료: [{pub_time}] {title[:25]}...")
                else:
                    print(f"⚠️ 전송 상태 이상: {res.status_code}")
            except Exception as e:
                print(f"❌ 전송 실패: {e}")

if __name__ == "__main__":
    fetch_and_send()
