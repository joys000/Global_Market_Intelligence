import feedparser
import requests
from datetime import datetime
from deep_translator import GoogleTranslator # 👈 번역 도구

# 네 렌더 서버 주소
SERVER_URL = "https://dividend-server.onrender.com/update_intel"

# 📡 사냥할 뉴스 창고들
NEWS_SOURCES = {
    "국내경제": "https://www.mk.co.kr/rss/30100041/",
    "해외경제": "https://www.investing.com/rss/news_285.rss",
    "해외속보": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000311" # CNBC 속보
}

def translate_text(text):
    """영어를 한국어로 번역하는 함수"""
    try:
        return GoogleTranslator(source='en', target='ko').translate(text)
    except:
        return text # 번역 실패시 원문 유지

def fetch_and_send():
    print(f"🚀 사냥 시작... {datetime.now()}")
    
    for category, url in NEWS_SOURCES.items():
        feed = feedparser.parse(url)
        # 각 소스당 최신 5개씩만 사냥
        for entry in feed.entries[:5]:
            title = entry.title
            
            # 🌐 해외 소스는 번역 거치기
            if category in ["해외경제", "해외속보"]:
                print(f"🔄 번역 중: {title[:20]}...")
                title = translate_text(title)

            news_data = {
                "type": "NEWS",
                "source": category,
                "title": title,
                "link": entry.link,
                "timestamp": datetime.now().strftime("%H:%M") # 현재 시간 기록
            }
            
            try:
                res = requests.post(SERVER_URL, json=news_data, timeout=10)
                if res.status_code == 200:
                    print(f"✅ 입고 완료: {title[:25]}...")
            except Exception as e:
                print(f"❌ 전송 실패: {e}")

if __name__ == "__main__":
    fetch_and_send()
